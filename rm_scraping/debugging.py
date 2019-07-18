from pprint import pprint

from rm_loader import RMLoader

loader = RMLoader(
    rm_kwargs=dict(debug=1)
)
def load(shortname):
  return loader.load_shortname(shortname)

#rm = load('sealevel')

