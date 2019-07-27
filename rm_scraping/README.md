Some code attempting to scrape and parse requested moves (RMs) in earnest. In `../requested_moves_counting.ipynb`, I used {{oldmoves}} templates and move logs to track the history of titles/RMs for controversial articles at a high level, but didn't attempt to scrape the RM discussions themselves. Here, I search talk pages for indications of RMs, and grab the whole wikitext of the section, and attempt to parse out structure such as:

- the original title of the article(s)
- the proposed new title(s)
- who nominated it
- who closed it, and what the outcome was
- how many times it was relisted
- who cast which votes
- who invoked which policies

See the `COLS` attributes in `RM.py` for the full "schema".

Runnable files are:
- `scrape.py`, which does the actual scraping and parsing, writing results to csv files
- `resolve_shortcuts.py` a quick post-processing step to generate a small ancillary csv that maps policy shortcuts (e.g. "WP:UCRN") to the full names of the pages they redirect to.
- `test_rms.py`, unit tests. Intended to be run using `pytest`.

## Scraping strategy

I find RM discussions by searching the 'Talk:' namespace for `<!-- Template:RM top -->` which is generated when substing the template which is used 99.9% of the time to close RM discussions. Unfortunately, there's a not-so-well-documented limit of 10,000 results for the MediaWiki search API (or technically, I guess the search backend used for Wikipedia), and there are more RMs than that. So I use a technique ([described here](https://www.mediawiki.org/wiki/API_talk:Search#Limit)) of constructing queries that partition the results into groups smaller than 10k (and accumulate results by appending to files in `scrape.py`).
