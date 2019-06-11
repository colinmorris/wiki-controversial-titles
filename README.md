Investigating/visualizing some of the longest debates over article titles on Wikipedia.

`moves.csv` lists all 421 mainspace talk pages which transclude the [Old moves](https://en.wikipedia.org/wiki/Template:Old_moves) template (as of June 2019). I downloaded it using [PetScan](https://petscan.wmflabs.org/). The 'Old moves' template is intended to list previous move discussions for an article, particularly for articles that have had many such discussions (to warn away editors who might unknowingly try to rehash old arguments).

From there, `requested_moves_counting.ipynb` does a bunch of stuff including:
- Heuristically parsing the contents of the 'Old moves' template (formatting is not always consistent) to estimate the number of past move discussions per article, as well as getting metadata about each move discussion (when it occurred, what new name was proposed, and what the outcome of the discussion was).
- Using `mwclient` to grab additional information through the MediaWiki API, particularly to query move logs (to get information about *undiscussed* moves in addition to ones that went through the formal Requested Move process)
- Visualizing the timelines of names for individual articles, combining the above information

There's also a bunch of manual cleaning of the data to account for numerous special cases and inconsistencies. For example, some articles have multi-branching histories. After the article originally at 'Chairman' was moved to 'Chair (officer)', a new, separate article was created at 'Chairman' (a "POV fork" in Wikipedia's jargon). Later, the two were merged.

`top50.txt` Gives the move history of the 50 most controversial article titles (as measured by number of move requests) in a 'human'-'readable' format. Several articles' listings are incomplete due to some technical issues with munging the move history, or inadequacies of the Wikimedia API. Also some seem misleadingly uncontroversial, because the file only lists times that the article actually moved (many articles have been fairly stable but have had a lot of heated Move Request discussions that failed to reach consensus).
