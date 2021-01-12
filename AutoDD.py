#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" AutoDD: Automatically does the so called Due Diligence for you. """

#AutoDD - Automatically does the "due diligence" for you.
#Copyright (C) 2020  Fufu Fang, Steven Zhu

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <https://www.gnu.org/licenses/>.

__author__ = "Fufu Fang" "kaito1410"
__copyright__ = "The GNU General Public License v3.0"

import argparse
import math
import os
import re
import sys
import pandas as pd
from datetime import datetime, timedelta
from timeit import default_timer as timer

import pandas as pd
from psaw import PushshiftAPI
from tabulate import tabulate
from yahooquery import Ticker

# dictionary of possible subreddits to search in with their respective column name
subreddit_dict = {'pennystocks' : 'pennystocks',
                  'RobinHoodPennyStocks' : 'RH_PennyStocks',
                  'Daytrading' : 'Daytrading',
                  'StockMarket' : 'StockMarket',
                  'stocks' : 'stocks'}

tagDict = {}

# dictionary of ticker financial information to get from yahoo
financial_measures = {'currentPrice' : 'Price', 'quickRatio': 'QuickRatio', 'currentRatio': 'CurrentRatio', 'targetMeanPrice': 'TargetMeanPrice', 'recommendationKey': 'RecommendationKey'}

# dictionary of ticker summary information to get from yahoo
summary_measures = {'previousClose' : 'PreviousClose', 'open': 'Open', 'dayLow': 'DayLow', 'dayHigh': 'DayHigh', 'payoutRatio': 'PayoutRatio', 'forwardPE': 'ForwardPE', 'beta': 'Beta', 'bidSize': 'BidSize', 'askSize': 'AskSize', 'volume': 'Volume', 'averageVolume': 'AverageVolume', 'averageVolume10days': 'AverageVolume10Days', 'fiftyDayAverage': '50DayAverage', 'twoHundredDayAverage': '200DayAverage'}


# dictionary of ticker financial information to get from yahoo - custom use.
financial_measures_custom = {'currentPrice' : 'Price', 'targetMeanPrice': 'TargetMeanPrice', 'recommendationKey': 'RecommendationKey'}

# dictionary of ticker summary information to get from yahoo - custom use.
summary_measures_custom = {'previousClose' : 'PreviousClose', 'open': 'Open', 'dayLow': 'DayLow', 'dayHigh': 'DayHigh', 'volume': 'Volume', 'averageVolume': 'AverageVolume'}


# note: the following scoring system is tuned to calculate a "popularity" score
# feel free to make adjustments to suit your needs

# x base point of for a ticker that appears on a subreddit title or text body that fits the search criteria
base_points = 4

# x bonus points for each flair matching 'DD' or 'Catalyst' of for a ticker that appears on the subreddit
bonus_points = 2

# every x upvotes on the thread counts for 1 point (rounded down)
upvote_factor = 2

def get_submission(n, sub):

    """
    Returns a list of results for submission in past:
    1st list: current result from n hours ago until now
    2nd list: prev result from 2n hours ago until n hours ago
    m. for each subreddit in subreddit_dict, create a new results list from 2n hours ago until now
     """

    # val = subreddit_dict.pop(sub, None)
    val = list(subreddit_dict.keys())[0]
    if val is None:
        print('invalid subreddit: ' + sub)
        quit()

    api = PushshiftAPI()

    mid_interval = datetime.today() - timedelta(hours=n)
    timestamp_mid = int(mid_interval.timestamp())
    timestamp_start = int((mid_interval - timedelta(hours=n)).timestamp())
    timestamp_end = int(datetime.today().timestamp())

    results = []
    # results from the last n hours
    results.append(api.search_submissions(after=timestamp_mid,
                                 before=timestamp_end,
                                 subreddit=sub,
                                 filter=['title', 'link_flair_text', 'selftext', 'score', 'url'])) 

    # results from the last 2n hours until n hours ago
    results.append(api.search_submissions(after=timestamp_start,
                                 before=timestamp_mid,
                                 subreddit=sub,
                                 filter=['title', 'link_flair_text', 'selftext', 'score', 'url'])) 

    # results for the other subreddits
    for key in subreddit_dict:
        results.append(api.search_submissions(after=timestamp_start,
                                    before=timestamp_end,
                                    subreddit=key,
                                    filter=['title', 'link_flair_text', 'selftext', 'score','url']))

    return results


def get_freq_list(gen):
    """
    Return the frequency list for the past n days

    :param int gen: The generator for subreddit submission
    :returns:
        - all_tbl - frequency table for all stock mentions
        - title_tbl - frequency table for stock mentions in titles
        - selftext_tbl - frequency table for all stock metninos in selftext
    """

    # Python regex pattern for stocks codes
    pattern = "[A-Z]{3,5}"

    # Dictionary containing the summaries
    all_dict = {}

    # looping over each thread
    for i in gen:

        # every ticker in the title will earn this base points
        increment = base_points

        # flair is worth bonus points
        if hasattr(i, 'link_flair_text'):
            if 'DD' in i.link_flair_text:
                increment += bonus_points
            if 'Catalyst' in i.link_flair_text:
                increment += bonus_points

        # every 2 upvotes are worth 1 extra point
        if hasattr(i, 'score') and upvote_factor > 0:
            increment += math.ceil(i.score/upvote_factor)

        # search the title for the ticker/tickers
        if hasattr(i, 'title'):
            title = ' ' + i.title + ' '
            title_extracted = set(re.findall(pattern, title))
  
            # title_extracted is a set, duplicate tickers from the same title counted once only
            for j in title_extracted:

                if j in all_dict:
                    all_dict[j] += increment
                else:
                    all_dict[j] = increment

        if hasattr(i, 'url'):
            url = ' ' + i.url + ' '

        # skip searching in text body if ticker was found in the title
        if len(title_extracted) > 0:
            continue

       # search the text body for the ticker/tickers
        if hasattr(i, 'selftext'):
            selftext = ' ' + i.selftext + ' '
            selftext_extracted = set(re.findall(pattern, selftext))

            for j in selftext_extracted:
                if j in tagDict:
                    tagDict[j].append(i.url)
                else:
                    tagDict.setdefault(j, [])

                if j in all_dict:
                    all_dict[j] += increment
                else:
                    all_dict[j] = increment

    return all_dict.items(), all_dict 

def filter_tbl(tbl, min_val):
    """
    Filter a frequency table

    :param list tbl: the table to be filtered
    :param int min: the number of days in the past
    :returns: the filtered table
    """
    BANNED_WORDS = [
        'THE', 'FUCK', 'ING', 'CEO', 'USD', 'WSB', 'FDA', 'NEWS', 'FOR', 'YOU', 'AMTES', 'WILL', 'CDT', 'SUPPO', 'MERGE',
        'BUY', 'HIGH', 'ADS', 'FOMO', 'THIS', 'OTC', 'ELI', 'IMO', 'TLDR', 'SHIT', 'ETF', 'BOOM', 'THANK', 'MAYBE', 'AKA',
        'CBS', 'SEC', 'NOW', 'OVER', 'ROPE', 'MOON', 'SSR', 'HOLD', 'SELL', 'COVID', 'GROUP', 'MONDA', 'PPP', 'REIT', 'HOT', 
        'USA', 'HUGE', 'CEO', 'NOOB', 'MONEY', 'WEEK', 'YOLO', 'LOW'
    ]

    tbl = [row for row in tbl if row[1][0] >= min_val or row[1][1] >= min_val]
    tbl = [row for row in tbl if row[0] not in BANNED_WORDS]
    return tbl


def combine_tbl(tbl_current, tbl_prev):
    """
    Combine two frequency table, one from the current time interval, and one from the past time interval
    :returns: the combined table
    """
    dict_result = {}

    for key, value in tbl_current:
        dict_result[key] = [value, value, 0, value]

    for key, value in tbl_prev:
        if key in dict_result.keys():
            dict_result[key][0] = dict_result[key][0] + value 
            dict_result[key][2] = value
            dict_result[key][3] = dict_result[key][3] - value 
        else:
            dict_result[key] = [value, 0, value, -value]

    return dict_result.items()


def additional_filter(results_tbl, filter_collection):

    _, filter_dict = get_freq_list(filter_collection)

    for k, v in results_tbl:
        if k in filter_dict.keys():
            v.append(filter_dict[k])
        else:
            v.append(0)
        
    return results_tbl


def get_list_val(lst, index):
        try:
            return lst[index]
        except IndexError:
            return 0


def print_tbl(tbl, args):

    for key, value in sorted(tagDict.items()):
        for k in pd.unique(value).tolist():
            print(key + " : " + k)

    header = ["Code", "Total", "Recent", "Prev", "Change"]
    header = header + list(subreddit_dict.values())

    if(args.custom):
        header = header + list(summary_measures_custom.values())
        header = header + list(financial_measures_custom.values())
    else:
        header = header + list(summary_measures.values())
        header = header + list(financial_measures.values())

    tbl = [[k] + v for k, v in tbl]

    now = datetime.now()
    # dd/mm/YY H:M:S
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

    #print("date and time now = ", dt_string)	
    #print(tabulate(tbl, headers=header))

    # save the file to the same dir as the AutoDD.py script
    completeName = os.path.join(sys.path[0], args.filename) 

    # Delete file if exists. We want fresh file everytime. No append.
    if os.path.exists(completeName):
        os.remove(completeName)

    # write to file
    with open(completeName, "a") as myfile:
        myfile.write('<!DOCTYPE html>')
        myfile.write('<html>')
        myfile.write('<head>')
        myfile.write('<link rel="stylesheet" href="style.css">')
        myfile.write('<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.3/jquery.min.js"></script>')
        myfile.write('</head>')
        myfile.write('<body>')
        myfile.write('<img src="rocketcrew_logo.jpg" class="center">')
        myfile.write('<h1>PennyStock AutoDD Scan</h1>')
        myfile.write('<div class="dbgOuter">')

        for key in subreddit_dict:
            if(key == 'RobinHoodPennyStocks'):
                myfile.write('<div class="dbgCont"><input type="checkbox" id="dbgRH_PennyStocks" class="dbgCheck" name="RH_PennyStocks" checked=""><label for="dbgRH_PennyStocks">RH_PennyStocks</label></div>')
            else:
                if(key == 'stocks' or key == 'Daytrading' or key ==  'StockMarket'):
                    myfile.write('<div class="dbgCont"><input type="checkbox" id="dbg'+key+'" class="dbgCheck" name="' + key + '"> <label for="dbg'+key+'">'+ key + '</label></div>')
                else:
                    myfile.write('<div class="dbgCont"><input type="checkbox" id="dbg'+key+'" class="dbgCheck" name="' + key + '" checked=""> <label for="dbg'+key+'">'+ key + '</label></div>')
          
        myfile.write('<button class="toggle">Show / Hide Stock Details</button>')
        myfile.write('</div>')
        myfile.write('<h1>' + dt_string + '</h1>')
        myfile.write(tabulate(tbl, headers=header, tablefmt="html"))

        for x in tagDict:
            myfile.write('<ul class="' + x + '">')
            for y in tagDict[x]:
                myfile.write('<li>' + y + '</li>')
            myfile.write('</ul>')


        for x in tagDict:
            myfile.write('<div id="' + x + '" class="overlay"> <div class="popup"> <a class="close" href="#">&times;</a> <div class="content">')
            myfile.write('<h1>Reddit Posts for: ' + x +'</h1>')
            for y in tagDict[x]:
                myfile.write('<a href="' + y + '">' + y + '</a> <br/>')
            myfile.write('</div></div></div>')

        myfile.write('<script src="sorttable.js"></script>')
        myfile.write('<script src="addclass.js"></script>')
        myfile.write('<script src="filters.js"></script>')
        myfile.write('</body>')
        myfile.write('</html> ')

       

    #logs to console
    print("Wrote to file successfully: ")
    print(completeName)



def get_nested(data, *args):
    if args and data:
        element  = args[0]
        if element:
            if type(data) == str:
                return 0
            value = data.get(element)
            return value if len(args) == 1 else get_nested(value, *args[1:])

def getTickerInfo(results_tbl):
    filtered_tbl = []

    for entry in results_tbl:
        ticker = Ticker(entry[0])
        if ticker is not None: 
            valid = False
            for measure in summary_measures.keys():
                result = get_nested(ticker.summary_detail, entry[0], measure)
                if result is not None:
                    entry[1].append(result)
                    if result != 0:
                        valid = True
                else:
                    entry[1].append(0)


            for measure in financial_measures.keys():
                result = get_nested(ticker.financial_data, entry[0], measure)
                if result is not None:
                    entry[1].append(result)
                    if result != 0:
                        valid = True
                else:
                    entry[1].append(0)

            if valid:
                filtered_tbl.append(entry)

    return filtered_tbl

def getCustomTickerInfo(results_tbl):
    filtered_tbl = []

    for entry in results_tbl:
        ticker = Ticker(entry[0])
        if ticker is not None: 
            valid = False
            for measure in summary_measures_custom.keys():
                result = get_nested(ticker.summary_detail, entry[0], measure)
                if result is not None:
                    entry[1].append(result)
                    if result != 0:
                        valid = True
                else:
                    entry[1].append(0)


            for measure in financial_measures_custom.keys():
                result = get_nested(ticker.financial_data, entry[0], measure)
                if result is not None:
                    entry[1].append(result)
                    if result != 0:
                        valid = True
                else:
                    entry[1].append(0)

            if valid:
                filtered_tbl.append(entry)

    return filtered_tbl

if __name__ == '__main__':
    start = timer()
    # Instantiate the parser
    parser = argparse.ArgumentParser(description='AutoDD Optional Parameters')

    parser.add_argument('--interval', nargs='?', const=24, type=int, default=24,
                    help='Choose a time interval in hours to filter the results, default is 24 hours')

    parser.add_argument('--min', nargs='?', const=10, type=int, default=10,
                    help='Filter out results that have less than the min score, default is 10')

    parser.add_argument('--adv', default=False, action='store_true',
                    help='Using this parameter shows advanced ticker information, running advanced mode is slower')

    parser.add_argument('--custom', default=False, action='store_true',
                    help='Using this parameter shows custom ticker information')

    parser.add_argument('--sub', nargs='?', const='pennystocks', type=str, default='pennystocks',
                    help='Choose a different subreddit to search for tickers in, default is pennystocks')

    parser.add_argument('--sort', nargs='?', const=1, type=int, default=1,
                    help='Sort the results table by descending order of score, 1 = sort by total score, 2 = sort by recent score, 3 = sort by previous score, 4 = sort by change in score')

    parser.add_argument('--filename', nargs='?', const='table_records.html', type=str, default='table_records.html',
                    help='Change the file name from table_records.txt to whatever you wish')

    args = parser.parse_args()

    print('Searching reddit submissions for DD/Catalyst and such...')
    results_from_api = get_submission(args.interval/2, args.sub)  

    print('Checking data for DD/Catalyst/Upvotes...')
    current_tbl, _ = get_freq_list(results_from_api[0])
    prev_tbl, _ = get_freq_list(results_from_api[1])

    print('Filtering data...')
    results_tbl = combine_tbl(current_tbl, prev_tbl)

    for api_result in results_from_api[2:]:
        results_tbl = additional_filter(results_tbl, api_result)

    results_tbl = filter_tbl(results_tbl, args.min)

    if args.sort == 1:
        results_tbl = sorted(results_tbl, key=lambda x: x[1][0], reverse=True)
    elif args.sort == 2:
        results_tbl = sorted(results_tbl, key=lambda x: x[1][1], reverse=True)
    elif args.sort == 3:
        results_tbl = sorted(results_tbl, key=lambda x: x[1][2], reverse=True)
    elif args.sort == 4:
        results_tbl = sorted(results_tbl, key=lambda x: x[1][3], reverse=True)

    if args.adv:
        print('Creating advance table from yahoo api..')
        results_tbl = getTickerInfo(results_tbl)
    
    if args.custom:
        print('Creating custom table from yahoo api...')
        results_tbl = getCustomTickerInfo(results_tbl)

    print_tbl(results_tbl, args)

    elapsed_time = timer() - start
    print('Took ' + str(elapsed_time) + ' seconds.')
