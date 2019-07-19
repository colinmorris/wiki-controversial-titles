import logging
import re

from base_comment import BaseComment
from constants import *
from exceptions import *

class Nomination(BaseComment):
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
    # nvm, make this a soft error, and handle it further up
    if len(froms) == 0:
      #raise FatalParsingException("No fromtos found in nom: {!r}".format(self.text))
      logging.warning("No fromtos found in nom: {!r}".format(
        self.text[:200]))
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

