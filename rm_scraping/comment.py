import dateparser
import logging
import re
from collections import Counter
import wikitextparser as wtp

from constants import *
from exceptions import *

class Comment(object):
  def __init__(self, text):
    # Leading and trailing whitespace should be totally ignorable.
    # (Most common cause: leaving a space between the start of their
    # text and the previous comment)
    self.text = text.strip()
    self.lines = self.text.split('\n')
    self.parsed = wtp.parse(self.text)

  def __repr__(self):
    return '<{} by {}: {!r}>'.format(
      self.__class__.__name__,
      self.author,
      self.text[:144],
      )
    
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
    # Third choice: a comment at any indentation level that starts with a bold token
    m = re.match(r"[\*\:]*\s*'''(.*?)'''", self.text)
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
  def find_comments(cls, text, include_sections=False, rm=True):
    acc = []
    if isinstance(text, list):
      lines = text
    else:
      lines = text.split('\n')

    found = 0
    for line in lines:
      if include_sections or not re.match('==.*==', line):
        acc.append(line)
      if cls.has_signature(line, nom=found==0):
        comment_text = '\n'.join(acc)
        if found == 0 and rm:
          # First comment of an rm is a Nom
          yield Nomination(comment_text)
        else:
          yield cls(comment_text)
        found += 1
        acc = []
    if 0 and acc: 
      # nvm, this is totally expected. Will normally end with hline, then "The above discussion
      # is preversed as an archive of a requested move..."
      logging.warning('Leftover non-comment matter after comments: {}'.format(acc))
      
  @staticmethod
  def has_signature(line, nom=False):
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
    buffer = 16
    if (utc_ix < len(line)-buffer 
        and ('Relist' not in line or not nom)
        and 'Autosigned' not in line
        and 'Template:Unsigned' not in line
        ):
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

  def get_close_outcome(self):
    """TODO: would be better to make another subclass for Closes
    """
    # First search for {{done}} or {{not done}} templates (see History of 
    # Palestine test case)
    m = re.search(r'{{((?:not )?done)}}', self.text)
    if m:
      return m.group(1)
    # if outcome is '''Moved''' look for 'to Foo' afterward.
    # (For cases where the outcome is to move the page to a title other than the one
    # proposed by nominator)
    m = re.search(r"'''Moved''' to \[\[(.*?)\]\]", self.text, re.IGNORECASE)
    if m:
      return 'Moved to {}'.format(m.group(1))
    return self.firstbold
  
  @property
  def firstbold(self):
    m = re.search("'''(.*?)'''", self.text, re.IGNORECASE)
    return m and m.group(1)


class Nomination(Comment):
  def __init__(self, text):
    self.fulltext = text
    # Looks like text can be Relisting or Relisted. https://en.wikipedia.org/wiki/Template:Relisting
    # Hope that hasn't changed over time....
    relist_prefix = "<small>--'''''Relist"
    relist_ix = text.find(relist_prefix)
    # NB: If our comment parsing routine has accidentally swallowed up a 
    # subsequent comment by a different user into the nom comment, this
    # will erase any trace of it.
    if relist_ix != -1:
      text = text[:relist_ix]
    self.relists = self.fulltext[relist_ix:].count(relist_prefix)
    super().__init__(text)

    self.parse_from_tos()

  def get_vote(self):
    assert False, "Nominations don't vote"

  def parse_from_tos(self):
    """Parse out the source article(s) and proposed destination title(s)
    """
    froms = []
    tos = []
    for line in self.lines:
      if RARROW in line:
        f, t = self.parse_fromto_line(line)
        froms.append(f)
        tos.append(t)
    if len(froms) == 0:
      raise FatalParsingException("No fromtos found in nom: {!r}".format(self.text))
    self.from_titles = froms
    self.to_titles = tos

  def parse_fromto_line(self, line):
    assert line.count(RARROW) == 1, "Too many rarrows: {!r}".format(line)
    i_arrow = line.find(RARROW)
    left = line[:i_arrow]
    m = re.search('\[\[:?(.*)\]\]', left)
    if not m:
      raise FatalParsingException(
        "Couldn't find from_title left of rarrow for line: {!r}".format(line)
      )
    frum = m.group(1)

    # Junk that can come before the to_title. Spaces. Single quotes (for rare cases where
    # nominator bolds or italicizes the to_title). Opening html tags (e.g. <u>)
    optional_prefix = r"[\s']*(?:<[a-zA-Z]>)?[\s']*"
    right = line[i_arrow+1:]
    # First check whether the original to title has been stricken through and replaced
    m = re.match(r'\s*<(s|del)>(.*?)</(s|del)>', right, re.IGNORECASE)
    struck_title = None
    if m:
      logging.warning("Found stricken-through text right of rarrow. Looking past it. right={!r}".format(right))
      struck_title = m.group(2)
      right = right[m.end():]
    # Most usual case: {{no redirect|foo}}. Also, rarely: 
    # - {{no redirect|1=foo}}
    # = {{noredirect|foo}}
    m = re.match(optional_prefix + r'{{no ?redirect\|(?:1=)?(.*?)}}', right)
    if m:
      return frum, m.group(1)
    # Less common: [[foo]]
    m = re.match(optional_prefix + r'\[\[:?(.*?)\]\]', right)
    if m:
      return frum, m.group(1)
    # Another fairly common case: ?
    # Used for 'open-ended' RMs, where nominator sees a good reason why the current
    # title is not appropriate, but doesn't want to restrict discussion to one specific
    # destination title.
    m = re.match(optional_prefix + r'\?', right)
    if m:
      return frum, None
    raise FatalParsingException("Couldn't find to_title in line: {!r}".format(line))

