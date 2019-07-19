import re
import logging
import dateparser
import wikitextparser as wtp
from collections import Counter

from constants import *
from exceptions import *

class BaseComment(object):

  def __init__(self, text):
    # Leading and trailing whitespace should be totally ignorable.
    # (Most common cause: leaving a space between the start of their
    # text and the previous comment)
    self.text = text.strip()
    self.lines = self.text.split('\n')
    self.parsed = wtp.parse(self.text)

  @property
  def extract(self):
    # Mostly used for logging
    return self.text[:200]
  
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
    # Yes, the underscore version is attested. I hate people.
    return 'User:' in line or 'User talk:' in line or 'User_talk:' in line

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
  
  @property
  def indentation(self):
    ind = 0
    for char in self.text:
      if char in ':*':
        ind += 1
      else:
        return ind
    
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
      if l.lower() in ('user', 'user talk', 'user_talk'):
        auth = r
        # In case they added a '#top' to the link or something
        if '#' in auth:
          auth = auth[:auth.find('#')]
        return auth
      
  @property
  def timestamp(self):
    # Example of non-standard time in signature:
    # https://en.wikipedia.org/wiki/Talk:KCLA_(Arkansas)#Defunct_radio_and_TV_station_disambiguator_changes_(consolidated)
    # Thanks a lot, Neutralhomer.
    tm = re.search("\d{2}:\d{2}(?:,|(?: on)) (\d{1,2}) ([A-Za-z]*) (\d{4})", self.text)
    if not tm:
      logging.warning("Couldn't parse signature timestamp. Using dummytime. {!r}".format(
        self.text[-200:]))
      return DUMMYTIME
    timestr = tm.group(0)
    return dateparser.parse(timestr)
  
  @property
  def firstbold(self):
    m = re.search("'''(.*?)'''", self.text, re.IGNORECASE)
    return m and m.group(1)
