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
