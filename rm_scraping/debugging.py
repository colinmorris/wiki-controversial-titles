import sys
from pprint import pprint
import argparse

from rm_loader import RMLoader

loader = RMLoader(
    rm_kwargs=dict(debug=1)
)
def load(shortname):
  return loader.load_shortname(shortname)

#parser = argparse.ArgumentParser()

#rm = load('sealevel')
if len(sys.argv) > 1:
  thing = sys.argv[1]
  print("Loading", thing)
  rm = loader.load(thing)
  rm.dissect()

