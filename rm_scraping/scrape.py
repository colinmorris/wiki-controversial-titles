import csv
import os
import mwclient
import argparse
import pandas as pd

from RM import RM
from constants import *

FLUSH_EVERY = 50
LIMIT = 0

NEXT_ID = 0

def scrape_rms_for_title(title, f_fail, debug=0):
  global NEXT_ID
  pg = wiki.pages[title]
  section_ix = 1
  while 1:
    try:
      section = pg.text(section=section_ix)
    except KeyError:
      break
    if RM.section_is_rm(section):
      try:
        yield RM(section, title, debug=debug, id=NEXT_ID)
      except Exception as e:
        row = '{}\t{}\n'.format(title, section_ix)
        f_fail.write(row)
        print('Exception:', e)
      else:
        NEXT_ID += 1
    section_ix += 1

def flush_rms(rms, rm_w, votes_w, pols_w):
  rm_w.writerows(rm.row for rm in rms)
  vote_rows = []
  pol_rows = []
  for rm in rms:
    for vote in rm.votes:
      vote['rm_id'] = rm.id
    vote_rows.extend(rm.votes)
    for user, counts in rm.user_to_policies.items():
      for pol, n in counts.items():
        row = dict(user=user, pol=pol, n=n, rm_id=rm.id)
        pol_rows.append(row)
  votes_w.writerows(vote_rows)
  pols_w.writerows(pol_rows)
    
if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-c', '--clobber', action='store_true', help='Overwrite existing csv files')
  parser.add_argument('-r', '--title-re', 
      help='Regex to add as an intitle filter to search query')
  parser.add_argument('--invert-titlematch', action='store_true', 
      help='Invert the intitle filter')
  args = parser.parse_args()
  if args.clobber:
    fresh = True
  else:
    try:
      st = os.stat('rms.csv')
    except FileNotFoundError:
      fresh = True
    else:
      fresh = st.st_size == 0
  extant_pages = set()
  if not fresh:
    df = pd.read_csv('rms.csv')
    NEXT_ID = df['id'].max() + 1
    print("Found existing files. Appending. Ids starting at {}".format(NEXT_ID))
    extant_pages = set(df['talkpage'].values)
  oflag = 'w' if fresh else 'a'
  frm = open('rms.csv', oflag)
  fvotes = open('votes.csv', oflag)
  fpols = open('pols.csv', oflag)
  out_rm = csv.DictWriter(frm, RM.COLS)
  out_votes = csv.DictWriter(fvotes, RM.VOTE_COLS)
  out_pols = csv.DictWriter(fpols, RM.POL_COLS)
  writers = [out_rm, out_votes, out_pols]
  if fresh:
    for wr in writers:
      wr.writeheader()

  wiki = mwclient.Site(('https', 'en.wikipedia.org'))

  query = 'insource:/"{}"/'.format(RMTOP)
  if args.title_re:
    query += ' {}intitle:/{}/'.format(
        ('-' if args.invert_titlematch else ''),
        args.title_re
    )
  results = wiki.search(query, namespace=1)

  rms = []
  failures = []
  f_fail = open('failures.tsv', oflag)
  i_pg = 0
  i_rm = 0
  skipped = 0
  for result in results:
    # Don't rescrape pages we've already done.
    if result['title'] in extant_pages:
      skipped += 1
      continue
    for rm in scrape_rms_for_title(result['title'], f_fail):
      rms.append(rm)
      i_rm += 1

    if len(rms) >= FLUSH_EVERY:
      flush_rms(rms, out_rm, out_votes, out_pols)
      rms = []

    if LIMIT and i_rm >= LIMIT:
      print("Reached limit. rms={}. Stopping".format(i_rm))
      break

    i_pg += 1
    if i_pg % 100 == 0:
      print("i_pg = {}; skipped = {}".format(i_pg, skipped))
      
  if rms:
    flush_rms(rms, out_rm, out_votes, out_pols)

  for f in [frm, fvotes, fpols, f_fail]:
      f.close()
  print("Skipped {} pages".format(skipped))
