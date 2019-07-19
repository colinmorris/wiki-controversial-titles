import datetime

RARROW = '→'
RMTOP = '<!-- Template:RM top -->'

# A time given to dummies who override default timestamp formatting in 
# their signatures.
DUMMYTIME = datetime.datetime.utcfromtimestamp(0)

# Value to use for attrs that may be accessible in the text, but which we couldn't
# parse out. (OTOH, we tend to use None for values that are known to have a semantically
# null value. e.g. mrv_date if no mrv was filed, vote.vote if the user didn't give any
# bolded recommendation)
UNKNOWN = '*UNK'
