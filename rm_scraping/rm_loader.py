import re
import os
import mwclient

import utils
from RM import RM

# Used for testing/debugging
SHORTNAME_TO_SLINK = dict(
    global_warming = 'Talk:List_of_scientists_who_disagree_with_the_scientific_consensus_on_global_warming#Requested_move_5_February_2018',
    sealevel = 'Talk:Metres_above_sea_level#Requested_move_16_December_2018',
    benghazi = 'Talk:2012_Benghazi_attack/Archive_4#Requested_move',
    ag2015 = 'Talk:War_in_Afghanistan_(2001–present)/Archive_12#Requested_move_1_October_2015',
    # NB: If we were perfect, we would probably class this as a multi-move. Seems like
    # nominator added another pair of titles in an unsigned bulleted comment right after
    # his nom. I think it's okay that we don't detect that too. It's janky.
    trinity = 'Talk:Trinity_College_Dublin/Archive_2#Requested_move',
    iraqwar_2016 = 'Talk:Iraq_War/Archive_32#Requested_move_23_June_2016',
    palestine_openmove = 'Talk:Foreign_relations_of_the_State_of_Palestine/Archive_7#Requested_move_(open_version)',
    # Example of a close that uses a {{not done}} template rather than bold text.
    hop_notdone = 'Talk:History_of_Palestine/Archive_2#Requested_move_30_July_2017',
    movedto='Talk:Ringelblum_Archive#Requested_move_20_June_2016',
    multimove='Talk:Cần_Thơ/Archive_1#Requested_move:_Removing_Vietnamese_Diacritics',
)
class RMLoader(object):

  def __init__(self, rm_cls=RM, rm_kwargs=None):
    wiki = mwclient.Site(('https', 'en.wikipedia.org'))
    self.wiki = wiki
    self.rm_cls = rm_cls
    self.rm_kwargs = rm_kwargs or {}

  def load(self, thing):
    if thing in SHORTNAME_TO_SLINK:
      return self.load_shortname(thing)
    return self.load_section_link(thing)

  def load_pg_and_section_ix(self, pgname, six):
    pg = self.wiki.pages[pgname]
    section = pg.text(section=six)
    return self.rm_cls(section, pgname, **self.rm_kwargs)

  def load_section_link(self, slink):
    txt = self.load_text_from_section_link(slink)
    pgname, anchor = slink.split('#')
    return self.rm_cls(txt, pgname, **self.rm_kwargs)

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
      # Make fixtures dir if necessary
      if not os.path.isdir('fixtures'):
        print("Making fixtures/ directory")
        os.mkdir('fixtures')
      slink = SHORTNAME_TO_SLINK[shortname]
      txt = self.load_text_from_section_link(slink)
      with open(fname, 'w') as f:
        f.write(txt)
      return txt

  def load_shortname(self, shortname):
    section = self.load_text_from_shortname(shortname)
    pgname, _ = SHORTNAME_TO_SLINK[shortname].split('#')
    return self.rm_cls(section, pgname, **self.rm_kwargs)


