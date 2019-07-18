import dateparser
import logging
import re
from collections import Counter
import wikitextparser as wtp

class Comment(object):
  def __init__(self, text):
    if isinstance(text, list):
      # er, nvm, self.lines not currently used.
      self.lines = text
      self.text = '\n'.join(text)
    else:
      self.text = text
      self.lines = text.split('\n')
    self.parsed = wtp.parse(self.text)
    self.nom = False

  def __repr__(self):
    return '<{} by {}: {!r}>'.format(
      ('Nom' if self.nom else 'Comment'),
      self.author,
      self.text[:144],
      )
    
  def set_nom(self):
    self.nom = True
    self.relists = 0
    # Need to re-evaluate given that text may contain some relisting notices at the end.
    # Looks like text can be Relisting or Relisted. https://en.wikipedia.org/wiki/Template:Relisting
    # Hope that hasn't changed over time....
    relist_prefix = "<small>--'''''Relist"
    relist_ix = self.text.find(relist_prefix)
    # NB: If our comment parsing routine has accidentally swallowed up a 
    # subsequent comment by a different user into the nom comment, this
    # will erase any trace of it.
    if relist_ix != -1:
      subtext = self.text[:relist_ix]
      orig_text = self.text
      self.text = subtext
      self.parsed = wtp.parse(subtext)
      self.relists = orig_text[relist_ix:].count(relist_prefix)
      
  def policy_counts(self):
    rex = r'(?:MOS|WP):[A-Z]+'
    counts = Counter()
    for pol in re.findall(rex, self.text):
      counts[pol] += 1
    return counts
      
  def get_vote(self):
    """Current heuristic is a little conservative. Will miss:
    - votes at indentation levels other than 1
    - votes that aren't bolded? (does that happen?)
    It will also often fail to capture some important context. e.g. from "'''Move''' to [[Foo]]"
    we'll just get "Move".
    """
    # The simplest case. Comment at indent level 1 starting with bolded text
    m = re.match(r"[\*\:]\s*'''(.*?)'''", self.text)
    if m:
      return dict(
        user=self.author,
        vote=m.group(1),
        date=self.timestamp.date(),
      )
    # Second choice: is this a multi-line comment where any of the lines match the above pattern? e.g.:
    # https://en.wikipedia.org/wiki/Talk:List_of_scientists_who_disagree_with_the_scientific_consensus_on_global_warming#Requested_move_5_February_2018
    # NewsAndEventsGuy's Support comment also gobbles up the section intro on the line above.
    m = re.search(r"^[\*\:]\s*'''(.*?)'''", self.text, re.MULTILINE)
    if m:
      return dict(
        user=self.author,
        vote=m.group(1),
        date=self.timestamp.date(),
      )
    # Include at least a dummy vote for any comment at indentation level 1.
    if self.indentation == 1:
      vote = ''
      for match in re.finditer(r"'''(.*?)'''", self.text):
        # Check that it's not stricken through
        if self.text[match.end():match.end()+4] == '</s>':
          continue
        meat = match.group(1)
        # Avoid false positives from bold in signatures
        if '[[User:' in meat or '[[User talk:' in meat:
          break
        vote = meat
        break
      return dict(
        user=self.author,
        vote=vote,
        date=self.timestamp.date(),
      )
  
  @property
  def indentation(self):
    ind = 0
    for char in self.text:
      if char in ':*':
        ind += 1
      else:
        return ind
    
  @classmethod
  def find_comments(cls, text, include_sections=False):
    acc = []
    if isinstance(text, list):
      lines = text
    else:
      lines = text.split('\n')

    for line in lines:
      if include_sections or not re.match('==.*==', line):
        acc.append(line)
      if cls.has_signature(line):
        yield cls(acc)
        acc = []
    if 0 and acc: 
      # nvm, this is totally expected. Will normally end with hline, then "The above discussion
      # is preversed as an archive of a requested move..."
      logging.warning('Leftover non-comment matter after comments: {}'.format(acc))
      
  @staticmethod
  def has_signature(line):
    # Quick and dirty heuristic. May need to improve.
    # Example relisted nom signature
    #  [[User:Fgnievinski|fgnievinski]] ([[User talk:Fgnievinski|talk]]) 04:35, 16 December 2018 (UTC)
    #  <small>--'''''Relisting.'''''&nbsp;–[[User:Ammarpad|Ammarpad]] ([[User talk:Ammarpad|talk]]) 
    #  04:55, 24 December 2018 (UTC)</small>
    
    # The below seems a little too restrictive. Found one example where there was a space after (UTC)
    #return line.endswith('(UTC)') or line.endswith('(UTC)</small>')
    utc_ix = line.rfind('(UTC)')
    if utc_ix == -1:
      return False
    # At one point had a heuristic where (UTC) needed to be "close enough" to
    # end of the line, but better to just be liberal. (Relists are what make
    # this especially complicated)
    buffer = 12
    if utc_ix < len(line)-buffer and 'Relist' not in line:
      logging.warning("Unusual 'signature'(?) with (UTC) not at end:\n{!r}".format(
        line))
    return 'User:' in line or 'User talk:' in line
    
  # Cache this? Probably doesn't matter.
  @property
  def author(self):
    # This should handle IP editors as well
    # Start from the end to account for pings etc.
    for link in reversed(self.parsed.wikilinks):
      t = link.target
      if ':' not in t:
        continue
      col_ix = t.find(':')
      l, r = t[:col_ix], t[col_ix+1:]
      if l in ('User', 'User talk'):
        auth = r
        # In case they added a '#top' to the link or something
        if '#' in auth:
          auth = auth[:auth.find('#')]
        return auth
      
  @property
  def timestamp(self):
    tm = re.search("\d{2}:\d{2}, (\d{1,2}) ([A-Za-z]*) (\d{4})", self.text)
    timestr = tm.group(0)
    return dateparser.parse(timestr)
  
  @property
  def firstbold(self):
    m = re.search("'''(.*?)'''", self.text)
    return m.group(1)
