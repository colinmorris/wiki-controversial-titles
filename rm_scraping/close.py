import logging
import re

from base_comment import BaseComment
from constants import *
from exceptions import *

class Close(BaseComment):
  """A closing comment.
  """
  @property
  def outcome(self):
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

