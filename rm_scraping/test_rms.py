from collections import Counter
import pytest_check as check

from RM import RM
from rm_loader import RMLoader


class RMTest(RM):
  """Wrapper around RM class adding a bunch of testing helpers.
  """
  def assert_no_mrv(self):
    self.assert_cols(
        mrv=0, mrv_date=None, mrv_result=None,
    )

  def assert_not_multi(self):
    self.assert_cols(
        all_froms='', all_tos='', n_articles=1,
    )

  def assert_cols(self, **kwargs):
    row = self.row
    for col, exp in kwargs.items():
      assert col in row, "Missing column {}".format(col)
      val = row[col]
      msg = col
      if col == 'n_participants':
        msg += ' ' + str(self.participants)
      check.equal(val, exp, msg)

  def assert_votecount(self, votecount):
    actual_vc = Counter(v['vote'] for v in self.votes)
    assert actual_vc == votecount

  def assert_user_pols(self, userpols):
    check.equal(self.user_to_policies, userpols)

  def assert_matching_votes(self, user_to_vote):
    found_users = set()
    for vote in self.votes:
      user = vote['user']
      if user in user_to_vote:
        check.equal(vote['vote'], user_to_vote[user])
        found_users.add(user)
    check.equal(
        set(user_to_vote.keys()),
        found_users
    )


loader = RMLoader(rm_cls=RMTest)
def load_rm(shortname):
  return loader.load_shortname(shortname)

# https://en.wikipedia.org/wiki/Talk:List_of_scientists_who_disagree_with_the_scientific_consensus_on_global_warming#Requested_move_5_February_2018
def test_global_warming():
  rm = load_rm('global_warming')
  rm.assert_no_mrv()
  rm.assert_not_multi()
  nag = 'NewsAndEventsGuy'
  rm.assert_cols(
      nominator=nag,
      closer='Dekimasu',
      outcome='consensus to move the page',
      n_relists=0,
      n_votes=7,
      from_title='List of scientists opposing the mainstream scientific assessment of global warming',
      to_title='List of scientists who disagree with the scientific consensus on global warming',
      talkpage='Talk:List_of_scientists_who_disagree_with_the_scientific_consensus_on_global_warming',
  )
  rm.assert_votecount({'Support': 7})

def test_sealevel():
  rm = load_rm('sealevel')
  rm.assert_cols(
      closer='Calidum',
      outcome='not moved',
      nominator='Fgnievinski',
      n_relists=1,
      n_comments=5,
      n_votes=5,
      n_participants=6,
  )

def test_benghazi():
  rm = load_rm('benghazi')
  rm.assert_cols(
      n_comments=8,
      n_participants=7,
      n_relists=0,
      n_votes=5,
      talkpage='Talk:2012_Benghazi_attack/Archive_4',
  )
  rm.assert_user_pols({
    'Richard-of-Earth': {'WP:CRITERIA': 1, 'WP:COMMONNAME': 1},
    'RightCowLeftCoast': {'WP:COMMONNAME': 1},
  })

def test_ag2015():
  rm = load_rm('ag2015')
  rm.assert_cols(
      n_comments=5,
      n_votes=5,
      n_participants=6,
  )

def test_trinity():
  rm = load_rm('trinity')
  rm.assert_cols(
      from_title='Trinity College, Dublin',
      to_title='Trinity College Dublin',
  )
  rm.assert_votecount({'Oppose': 2})

def test_iraqwar_2016():
  rm = load_rm('iraqwar_2016')
  rm.assert_matching_votes({
    'Shhhhwwww!!': 'Support',
  })

def test_openmove():
  # An rm to '?'
  rm = load_rm('palestine_openmove')
  rm.assert_cols(
      from_title='Foreign relations of the Palestinian National Authority',
      to_title=None,
  )

def test_notdone():
  rm = load_rm('hop_notdone')
  rm.assert_cols(
      closer='DrStrauss',
      outcome='not done',
  )

def test_movedto():
  rm = load_rm('movedto')
  rm.assert_cols(
      from_title='Oyneg Shabbos',
      to_title='Oyneg Shabbos (group)',
      outcome='Moved to Ringelblum Archive',
  )

def test_multimove():
  rm = load_rm('multimove')
  rm.assert_cols(
      to_title='Can Tho',
      n_articles=14,
      all_tos='Can Tho|Ca Mau|Cao Lanh|My Tho|Nam Dinh|Phan Thiet|Quang Ngai|Rach Gia|Thai '
        'Nguyen|Thanh Hoa|Thu Dau Mot|Vinh Yen|Vung Tau|Yen Bai',
  )

def test_weirdclose():
  rm = load_rm('weirdclose')
  rm.assert_cols(
      closer='BD2412',
      outcome='Moved per consensus',
      from_title='Academy Award',
      to_title='Academy Awards',
      nominator='CrunchySkies',
  )

def test_boldto():
  rm = load_rm('boldto')
  rm.assert_cols(
      to_title='Władysław II Jagiełło',
  )

def test_nored():
  rm = load_rm('nored')
  rm.assert_cols(
      from_title='Nick Nemeth',
      to_title='Dolph Ziggler',
  )

def test_nocomms():
  rm = load_rm('nocomms')
  rm.assert_cols(
      outcome='page moved',
      n_votes=0,
      n_comments=0,
      n_participants=1,
  )

def test_multiqmarks():
  rm = load_rm('multi_qmarks')
  rm.assert_cols(
      # Have to admit, I didn't count. Just trusting this is right.
      n_articles=79,
      all_tos='|'.join('None' for _ in range(79)),
  )

def test_talkative_closer():
  # RM where the closer left an additional message after their closing message
  rm = load_rm('talkative_closer')
  rm.assert_cols(
      closer='StraussInTheHouse',
      outcome='Not moved',
      nominator='SelfieCity',
      n_relists=0,
  )

def test_withdrawn():
  rm = load_rm('withdrawn')
  rm.assert_cols(
      outcome='Withdrawn/snow by nom.',
      closer='Dicklyon',
      nominator='Dicklyon',
      n_articles=3,
  )

def test_user_underscore_talk():
  rm = load_rm('user_talk')
  rm.assert_cols(
      outcome='not moved',
      closer='Bradv',
      from_title='2015 Thalys train attack',
      to_title='Thalys train attack',
  )
