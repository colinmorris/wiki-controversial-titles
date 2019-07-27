import pandas as pd
import time
import mwclient
import wikitextparser as wtp

debug = 0
WRITE = (not debug) or 0

def pol_to_row(pol):
  pg = wiki.pages[pol]
  if not pg.redirect:
    # Justification: let's say expanded is the canonical title of the page
    # corresponding to the shortcut. If the shortcut is a redlink, that doesn't
    # exist (i.e. is None). If it exists but isn't a redirect, then it's the
    # "shortcut" name itself (though with the WP prefix expanded)
    if pg.pageid is None:
      #print("WARNING: {!r} is not a page at all".format(pol))
      expanded = None
    else:
      #print("WARNING: {!r} is not a redirect".format(pol))
      expanded = pg.name
  else:
    parsed = wtp.parse(pg.text())
    links = parsed.wikilinks
    if len(links) > 1:
      print("XXX: More than 1 link in redirect page: {!r}".format(pol))
    link = links[0]
    expanded = link.target.replace('_', ' ')
    
    dest = pg.redirects_to()
    if link.title.replace('_', ' ').replace('WP:', 'Wikipedia:') != dest.name:
      print("Super-warning: mismatch between {!r} and {!r} for pol={}".format(
        link.target, dest.name, pol
        ))
    if not expanded.startswith('Wikipedia'):
      print("Non-WP redirect target: {}".format(expanded))
  row = dict(
      pol=pol,
      expanded=expanded,
  )
  return row


t0 = time.time()
w = wiki = mwclient.Site(('https', 'en.wikipedia.org'))

df = pd.read_csv('pols.csv')
pol_to_count = df.groupby('pol')['n'].sum().to_dict()
all_pols = df.pol.unique()
print("Loaded {} unique policy shortcuts".format(len(all_pols)))

rows = []

# Map from expanded page titles to their 'canonical' shortcuts (i.e. the one
# most frequently used to link to it).
exp_to_canon = {}

for pol in all_pols[:(5 if debug else None)]:
  row = pol_to_row(pol)
  row['n'] = pol_to_count[pol]
  rows.append(row)

  xp = row['expanded']
  if xp in exp_to_canon:
    _, n = exp_to_canon[xp]
  else:
    n = 0
  if row['n'] > n:
    exp_to_canon[xp] = (pol, row['n'])

for row in rows:
  if row['expanded'] is None:
    row['canon'] = row['pol']
  else:
    row['canon'] = exp_to_canon[row['expanded']][0]

out = pd.DataFrame(rows)
if WRITE:
  out.to_csv('shortcuts.csv', index=False)

t1 = time.time()
print("Finished in {:.1f} seconds".format(t1-t0))
