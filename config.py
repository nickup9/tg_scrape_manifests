# Possible values for server: manuel, sybil, terry. I mean, it could
#    be others I imagine but eh.
# year must be int - determine bound lower bound to scrape from
#    <now> to the year, inclusive.
# jobs must be a list, case sensitive. Fuck you, type it out.
# download_okay is a bool - determine if we should update our side of
#    logs or not. We didn't need to keep up to date records, anyways
# hard_reset determines if we don't want to bother checking, and just
#    redownload data as bounded
# player_pop determines the threshold over which we'll include a
#    given round in analysis. Note that we'll still download rounds below
#    the threshold anyways - we just won't analyze data from them.
import os

class Config:
    server = 'manuel'
    year = 2022
    jobs = ['Assistant']
    download_okay = True
    base_url = f'https://tgstation13.org/parsed-logs/{server}/data/logs/'
    hard_reset = False
    data_path = os.path.join(os.path.dirname(__file__), 'data')
    player_pop = 40