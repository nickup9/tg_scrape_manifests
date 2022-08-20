from genericpath import isfile
import os
import requests
import shutil
import statistics

from datetime import datetime
from config import Config

# Data is stored in __file__ dir/data
# Data gets catagorized by year, then month. There's no folders for dates.
# Results gets overwritten every run, saved at top level of data.

# Metrics: 
#   Time: A long-ass time if you're starting from scratch lol
#       Otherwise not too shabby I'd reckon.
#   Amt data downloaded: About 1.25 MB per month, give or take 1/4 a meg
#   Bandwidth: Requests are made for each year, month, and day to build the dict 
#       (or list for the case of days) of loggable days/months/years, 
#       then we download all manifests for all days for all 
#       months that are missing
#   Okay but what's the numbers: Fuck if I know
def main():
    print('startup')
    possible_months = get_months()

    if os.path.exists(Config.data_path) == False:
        print('Making data dir')
        os.makedirs(Config.data_path)
    
    # To redownload all data (takes a long time) (maybe don't do this)
    if Config.hard_reset:
        verify = input("""Hey, you're about to rm all data then replace it.
        Are you sure you want to do this? This will take some time!
        Enter 'Yes' or 'yes' to confirm.""")
        if (verify != 'Yes') or (verify != 'yes'):
            raise('Aborting')
        shutil.rmtree(Config.data_path)
        os.makedirs(Config.data_path)
        get_data(possible_months)
        analyze_data(possible_months)

    else:
        missing_months = check_if_existing(possible_months)
        # Hey, we okay to download?
        if Config.download_okay:
            print('Getting missing data, please be patient')
            print(f'Missing data: {missing_months}')
            get_data(missing_months)
            print('Beginning analyisis')
            analyze_data(possible_months)
        # Work with what we got
        else:
            present_months = filter(lambda i: i not in missing_months, possible_months)
            analyze_data(present_months)

# Check to see what months we're missing
def check_if_existing(months_dict):
    missing_months = {}
    for year in months_dict.keys():
        missing_months[year] = []
        for month in months_dict[year]:
            month_path = os.path.join(Config.data_path, str(year), month)
            if os.path.exists(month_path) == False:
                missing_months[year].append(month)
    return missing_months

# Get actual manfifests
def get_data(months_dict):
    for year in months_dict.keys():
        print(f'Getting year: {year}')
        for month in months_dict[year]:
            print(f'Getting month: {month}')
            month_path = os.path.join(Config.data_path, str(year), month)
            os.makedirs(month_path)
            days = get_days(year, month)
            for day in days:
                url = f'{Config.base_url}/{year}/{month}/{day}?index_format=json'
                response = try_request(url)
                response = response.json()
                for x in response:
                    # See if this is a dir for a round, not something else
                    round = x['name']
                    if ('round' in x['name']) and ('zip' not in x['name']):
                        url = f'{Config.base_url}/{year}/{month}/{day}/{round}/manifest.txt'
                        response = try_request(url)
                        # Note: we're not making a folder for each day
                        # This is because we're lookin more long term, kinda.
                        # I might want to reconsider tho
                        with open(os.path.join(month_path, f'{round}_manifest.txt'), 'w') as f:
                            f.write(response.text)

# Analyze data, spit out results based on month, year, and all data.
def analyze_data(months_dict):
    with open(os.path.join(Config.data_path, f'results.txt'), 'w') as res_file:
        res_file.write(f'Getting results with the jobs {Config.jobs} \n\n')
        all_data = []
        for year in months_dict.keys():
            year_data = []
            for month in months_dict[year]:
                month_data = []
                for fname in os.listdir(os.path.join(Config.data_path, str(year), month)):
                    fname_loc = os.path.join(Config.data_path, str(year), month, fname)
                    with open(fname_loc, 'r') as f:
                        lines = f.readlines()
                        # -3 due to lines we don't want being present
                        if (len(lines) - 3) >= Config.player_pop:
                            num_occur = read_manifest_lines(lines)
                            year_data.append(num_occur)
                            month_data.append(num_occur)
                            all_data.append(num_occur)
                month_median = statistics.median(month_data)
                month_mean = statistics.mean(month_data)
                res_file.write(f'---Year {year} month {month}---\n')
                res_file.write(f'median: {month_median} mean: {month_mean}\n')
            year_median = statistics.median(year_data)
            year_mean = statistics.mean(year_data)
            res_file.write(f'\n----Year {year}----\n')
            res_file.write(f'median: {year_median} mean: {year_mean}\n\n')
        median = statistics.median(all_data)
        mean = statistics.mean(all_data)
        res_file.write(f'\nAll\n')
        res_file.write(f'median: {median} mean: {mean}\n')
            
# Get a dict of all months in a given year.
# Necessary since if you're looking at the current year, there's prolly not
#    all 12 months to pull from.
def get_months():
    cur_year = datetime.now().year
    possible_months = {}

    while cur_year >= Config.year:
        # breakpoint()
        possible_months[cur_year] = []
        url = url = f'{Config.base_url}/{cur_year}?index_format=json'
        response = try_request(url)
        if response.ok:
            response = response.json()
            for x in response:
                possible_months[cur_year].append(x['name'])
        cur_year = cur_year - 1
    return possible_months

# Get all logged days in a month
def get_days(year, month):
    days = []
    url = f'{Config.base_url}/{year}/{month}?index_format=json'
    response = try_request(url)
    response = response.json()
    for x in response:
        if '.txt.' not in x['name']:
            days.append(x['name'])
    return days

# Necessary since sometimes TG leaves me on read, and we need to retry
def try_request(url):
    attempts = 0
    while attempts < 5:
        try:
            response = requests.get(url, timeout = 2)
            return response
        except:
            print(f'retrying {attempts}/5...')
            attempts = attempts + 1
    raise TimeoutError('Timed out while scraping data!')

# Read lines (from a file, ideally) and see how many times a job from
#    jobs is in said file
def read_manifest_lines(lines):
    occur = 0
    for line in lines:
        if any(job in line for job in Config.jobs):
            occur = occur + 1
    return occur


if __name__ == '__main__':
    main()
