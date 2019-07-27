import dateparser
import pprint
import logging
import re
from collections import defaultdict, Counter
import wikitextparser as wtp

from comment_extractor import CommentExtractor
from constants import *
from exceptions import *

def parse_anchor(anchor):
  s = anchor.strip()
  s = s.replace(' ', '_')
  return s

def find_template(parsed, name):
  for t in parsed.templates:
    if t.name == name:
      return t

class RM(object):
  ROW_DEFAULTS = dict(
    mrv_date=None,
    mrv_result=None,
    mrv=0,
    n_articles=1,
    all_froms='',
    all_tos='',
  )
  COLS = [
      'from_title', 'to_title', # None if right-hand-side of arrow is '?'
      'rm_link', # e.g. "Talk:Cheryl_(singer)/Archive_3#Rename_request_4"
      # Article this RM's talk page belongs to (just the above but stripped of
      # Talk: prefix, and any subpage suffix and anchor)
      'article', 'talkpage',
      'id', # Unique id for this RM (currently same as rm_link)
      'nom_date', 'nominator', 
       'close_date', 'closer', 'outcome', 'n_relists',
      # Move review stuff. mrv = 1 if there was a review.
      'mrv', 'mrv_date', 'mrv_result',
      # Size of RM discussion measured in various units
      'chars', 
      'n_comments', # Does not include nomination or close
      'n_participants', # Not counting closer or relisters - but including nominator (which is kinda silly I guess...)
      # n_votes is just the length of self.votes. So NB that it includes
      # level-1 comments even if they don't begin with a bolded !vote.
      # Multiple 'votes' from the same user are deduped.
      'n_votes',
      # n_articles > 1 means this is a multimove. all_froms and all_tos are pip-separated strs.
      # in this case, from_title and to_title are just the first listed move.
      'n_articles', 'all_froms', 'all_tos', 
  ]
  VOTE_COLS = ['user', 'vote', 'date', 'rm_id']
  POL_COLS = ['user', 'pol', 'n', 'rm_id']

  def __init__(self, section, pagename, debug=0, id=None):
    self.debug = debug
    self.text = section
    self.lines = self.text.split('\n')
    self.where = 0 # current line number
    self.parsed = wtp.parse(section)
    pre = 'Talk:'
    assert pagename.startswith(pre)
    self.row = self.ROW_DEFAULTS.copy()
    self.row['article'] = pagename[len(pre):(pagename.find('/') if '/' in pagename else None)]
    self.row['rm_link'] = pagename + '#' + parse_anchor(self.parsed.sections[1].title)
    # I know, I know, a lot of redundancy going on.
    self.row['talkpage'] = pagename
    self.log_val(url = self.url)
    self.row['chars'] = len(section)
    # List of dicts having keys vote, user
    self.votes = []
    # Mapping from usernames to dict counters of ocurrences of citations of policy (WP:FOO)
    self.user_to_policies = defaultdict(lambda: Counter())
    # A unique identifier for this RM. Used as a 'foreign key' for vote/pols data.
    if id is not None:
      self.id = str(id)
    else:
      # More readable, but much less space-efficient. Not sure if that'll matter.
      # WP:RECOGNIZABILITY vs. WP:CONCISENESS. lol.
      # NB: In rare cases, this is actually non-unique. e.g.
      # https://en.wikipedia.org/wiki/Talk:Poppy_(entertainer)#Requested_move_20_May_2017
      self.id = self.row['rm_link']
    self.row['id'] = self.id
    
    self.parse()
    
  def __str__(self):
    return 'Requested Move: {} → {} {}'.format(
      self.row['from_title'], self.row['to_title'],
      self.row['nom_date'],
    )
  
  def __repr__(self):
    return str(self)
  
  @property
  def url(self):
    # Yeah, there's more to do here...
    suff = self.row['rm_link'].replace(' ', '_')
    return 'https://en.wikipedia.org/wiki/' + suff
  
  def dissect(self):
    ordered_pairs = [(k, self.row[k]) for k in self.COLS]
    pprint.pprint(ordered_pairs)
    print("#### Votes ####")
    pprint.pprint(self.votes)
    print("#### Polquotes ####")
    pprint.pprint(self.user_to_policies)
    
  def set(self, k, v):
    self.log('Setting {}={!r}'.format(k, v))
    self.row[k] = v
    
  def setn(self, **kwargs):
    for k, v in kwargs.items():
      self.set(k, v)
  
  @classmethod
  def section_is_rm(cls, sect):
    # Bottleneck?
    # only count top-level discussions
    return sect[2] != '=' and RMTOP in sect
  
  def log(self, msg):
    if self.debug:
      print(msg)
      
  def log_val(self, **kwargs):
    for k, v in kwargs.items():
      msg = '{}={!r}'.format(k, v)
      self.log(msg)
      
  def log2(self, **kwargs):
    if self.debug > 1:
      self.log_val(**kwargs)
  
  def warn(self, msg):
    msg += ' for {}'.format(self.url)
    logging.warning(msg)
  
  def parse(self):
    self.check_mrv()
    self.extracted = CommentExtractor(self.text)
    self.parse_close()
    self.parse_nom(self.extracted.nom)
    self.parse_discussion(self.extracted.comments)

  def parse_nom(self, nom):
    """
    - nom stuff (line immediately below hline)
  - from title
  - proposed title (if any)
  - other corresp moves (if multi-nom)
  - date RM opened
  - nominator
  - n relists (though I think sometimes these can occur further down rather than by nom?)
    """
    self.log_val(nominator_comment=nom.extract)

    froms, tos = nom.from_titles, nom.to_titles
    if len(froms) > 1:
      # Multi-move
      self.setn(
        n_articles=len(froms),
        all_froms='|'.join(map(str, froms)),
        all_tos='|'.join(map(str, tos)),
      )
    mainfrom = UNKNOWN if len(froms) == 0 else froms[0]
    mainto = UNKNOWN if len(tos) == 0 else tos[0]
    self.setn(
      nom_date=nom.timestamp,
      from_title=mainfrom,
      to_title=mainto,
      n_relists=nom.relists,
    )
    nominator=nom.author
    polcounts = nom.policy_counts()
    if polcounts:
      self.user_to_policies[nominator].update(polcounts)
    self.setn(nominator=nominator)
    
  def parse_discussion(self, comments):
    """Populate columns related to volume of discussion. Also populate self.votes.
    """
    participants = {self.row['nominator']}
    n_comments = 0 # Don't count nom
    for comment in comments:
      auth = comment.author
      participants.add(auth)
      n_comments += 1
      vote = comment.get_vote()
      if vote:
        self.votes.append(vote)
      self.log2(
        comment=comment.text,
        vote=vote,
      )
      polcounts = comment.policy_counts()
      if polcounts:
        self.user_to_policies[auth].update(polcounts)
        
    self._merge_votes()
    self.participants = participants # for debugging
    self.setn(
      n_votes=len(self.votes),
      n_comments=n_comments,
      n_participants=len(participants),
    )
    
  def _merge_votes(self):
    """Collapse multiple votes by a single user to one, which we try to choose to be the
    most 'significant' one. e.g. if one is "Comment" and the other is "Oppose", we'll take
    the latter.
    """
    user_to_power_and_ix = {}
    # TODO: add to this as more examples are observed
    vote_kws = {'support', 'oppose', 'neutral', 'move', 'close'}
    for i, vote in enumerate(self.votes):
      rec = vote['vote'].lower()
      if rec == '':
        power = 0
      else:
        if any(kw in rec for kw in vote_kws):
          power = 2
        else:
          # For bold things not recognizable as reccs (e.g. '''Comment''')
          power = 1
      self.log_val(
        vote=vote,
        power=power
      )
      user = vote['user']
      bestpow, _ = user_to_power_and_ix.get(user, (-1, 0))
      if power > bestpow:
        self.log('Updating best vote. pow {} > {}'.format(power, bestpow))
        user_to_power_and_ix[user] = (power, i)
        
    newvotes = [self.votes[i] for (_, i) in user_to_power_and_ix.values()]
    self.votes = newvotes
    
  def check_mrv(self):
    """Check for an existence of a Move Review template. If found, set some related cols."""
    for template in self.parsed.templates:
      if template.name == 'move review talk':
        date_arg = template.get_arg('date')
        if date_arg:
          date_str = date_arg.value
          self.set('mrv_date', dateparser.parse(date_str).date())
        else:
          self.warn('MRV missing date arg: {}'.format(template.string))
        result = template.get_arg('result')
        if result:
          res = result.value.strip()
        else:
          res = ''
          self.warn('MRV missing result arg: {}'.format(template.string))
        self.set('mrv_result', res)
        self.set('mrv', 1)
        return
  
  def parse_close(self):
    """Parse attrs related to closing statement: 
    - closer (and whether admin) {{RMnac}} - always supposed to be substed tho. Same w {{RMpmc}}
      - let's leave those flags out for now
    - date RM closed
    - close outcome (moved, not moved, no consensus, withdrawn, ...)
    """
    close = self.extracted.close
    self.log_val(close_str=close.text[:200])
    self.setn(
      closer=close.author,
      close_date=close.timestamp,
      outcome=close.outcome,
    )    
