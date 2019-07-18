import re
import os
import mwclient

import utils
from RM import RM

# Used for testing/debugging
SHORTNAME_TO_SLINK = dict(
    global_warming = 'Talk:List_of_scientists_who_disagree_with_the_scientific_consensus_on_global_warming#Requested_move_5_February_2018',
    sealevel = 'Talk:Metres_above_sea_level#Requested_move_16_December_2018',
)
class RMLoader(object):

  def __init__(self, rm_cls=RM, rm_kwargs=None):
    wiki = mwclient.Site(('https', 'en.wikipedia.org'))
    self.wiki = wiki
    self.rm_cls = rm_cls
    self.rm_kwargs = rm_kwargs or {}

  def load_text_from_section_link(self, slink):
    pgname, anchor = slink.split('#')
    stitle = utils.urldecode(anchor)
    pg = self.wiki.pages[pgname]
    i = 1
    while 1:
      section = pg.text(section=i)
      m = re.match('==+\s*(.*?)\s*==+', section)
      if m and m.group(1) == stitle:
        return section
      i += 1
      
  def load_text_from_shortname(self, shortname):
    fname = os.path.join('fixtures', shortname+'.wiki')
    try:
      f = open(fname)
      return f.read()
    except FileNotFoundError:
      slink = SHORTNAME_TO_SLINK[shortname]
      txt = self.load_text_from_section_link(slink)
      with open(fname, 'w') as f:
        f.write(txt)
      return txt

  def load_shortname(self, shortname):
    section = self.load_text_from_shortname(shortname)
    pgname, _ = SHORTNAME_TO_SLINK[shortname].split('#')
    return self.rm_cls(section, pgname, **self.rm_kwargs)


