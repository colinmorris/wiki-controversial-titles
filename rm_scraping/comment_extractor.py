import re
import logging

from base_comment import BaseComment
from comment import Comment
from nomination import Nomination
from close import Close
from constants import *

class CommentExtractor(object):
  """Decomposes an RM into a bunch of Comment instances.

  Okay, I guess I didn't really need a class for this, but whatever.
  """

  def __init__(self, text):
    self.text = text
    self.lines = self.text.split('\n')
    self.comments = []

    self.parse()

  @staticmethod
  def matches_archivemsg(line):
    phrases = [
        'The following is a closed discussion',
        'The following discussion is an archived',
    ]
    return any(phrase in line for phrase in phrases)

  def parse(self):
    i = 0
    lines = self.lines
    # Typical layout of top matter:
    # <div class="boilerplate" .... Template:RM top -->
    # :''The following is an archive discussion...
    # [blank line]
    # closer comment
    # hline
    # blank line
    # nom
    # ... but the blank lines and hlines are more or less optional
    i_rmtop = -1
    i_archive_msg = -1
    a_close = -1
    b_close = -1
    while i < len(lines):
      line = lines[i]
      if '<!-- Template:RM top -->' in line:
        i_rmtop = i
        break
      i += 1
    arch = lines[i_rmtop+1]
    if not self.matches_archivemsg(arch):
      logging.warning("Line immediately following RM top doesn't look like"
          "archive msg: {!r}".format(arch[:400]))
      
    i = i_rmtop+2
    acc = []
    # Postcondition: self.close is set, and i is idx of last line of close
    while i < len(lines):
      line = lines[i]
      if line != '' and line != '----':
        acc.append(line)

      if BaseComment.has_signature(line):
        if len(acc) != 1:
          logging.warning("Got >1 line for closing comment: {!r}".format(
            [accline[:200] for accline in acc]))
        close_txt = '\n'.join(acc)
        self.close = Close(close_txt)
        break

      i += 1

    # Get nom comment (absorbing any intervening comments from closer)
    i += 1 # Advance to first line after close
    acc = []
    while i < len(lines):
      line = lines[i]
      if line != '' and line != '----':
        acc.append(line)
      if BaseComment.has_signature(line):
        nom_text = '\n'.join(acc)
        # Bit of a hack
        test_comm = BaseComment(nom_text)
        # If this is a comment by the closer, it's not the nom. *UNLESS the
        # nominator is withdrawing*. If there's a rarrow in the text, let's
        # assume it is the latter case.
        if test_comm.author == self.close.author and RARROW not in nom_text:
          acc = []
        else:
          self.nom = Nomination(nom_text)
          break

      i += 1
    # Postcondition: close and nom are set. i is idx of last line of nom.
    # Everything after this should be a comment.
    acc = []
    for line in lines[i+1:]:
      # For simplicity, ignore section headings, hlines, and blank lines.
      if line != '' and line != '----' and not re.match('==.*==', line):
        acc.append(line)
      if BaseComment.has_signature(line):
        text = '\n'.join(acc)
        c = Comment(text)
        self.comments.append(c)
        acc = []
