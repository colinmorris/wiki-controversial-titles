import urllib.parse

def urlencode(s):
  s2 = s.replace(' ', '_')
  return urllib.parse.quote(s2)

def urldecode(s):
  return urllib.parse.unquote(s).replace('_', ' ')
