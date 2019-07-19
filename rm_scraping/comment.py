import logging
import re

from base_comment import BaseComment
from constants import *
from exceptions import *

class Comment(BaseComment):
  """A comment in an RM discussion which is neither a nomination or a close.
  Generally this will be one of:
  - a !vote at indentation level 1, beginning with a bolded recommendation
  - a comment at indentation level 1 (possibly in a separate 'discussion' section
    from the survey section). No bolded recc. Or bolded '''comment'''.
  - a reply to one of the above (or a reply to a reply to...)
  """

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
  


