
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from datetime import datetime as datetime  # For datetime objects
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

# Import the backtrader platform
import backtrader as bt
import model
import numpy as np
from scipy.signal import argrelextrema

from collections import defaultdict

def find_patterns(max_min):  
    patterns = defaultdict(list)
    
    # Window range is 5 units
    for i in range(5, len(max_min)):  
        window = max_min.iloc[i-5:i]
        
        # Pattern must play out in less than n units
        if window.index[-1] - window.index[0] > 100:      
            continue   
            
        a, b, c, d, e = window.iloc[0:5]
                
        # IHS
        if a<b and c<a and c<e and c<d and e<d and abs(b-d)<=np.mean([b,d])*0.02:
               patterns['IHS'].append((window.index[0], window.index[-1]))
        
    return patterns



def get_max_min(prices, smoothing, window_range):
    smooth_prices = prices['close'].rolling(window=smoothing).mean().dropna()
    local_max = argrelextrema(smooth_prices.values, np.greater)[0]
    local_min = argrelextrema(smooth_prices.values, np.less)[0]
    price_local_max_dt = []
    for i in local_max:
        if (i>window_range) and (i<len(prices)-window_range):
            price_local_max_dt.append(prices.iloc[i-window_range:i+window_range]['close'].idxmax())
    price_local_min_dt = []
    for i in local_min:
        if (i>window_range) and (i<len(prices)-window_range):
            price_local_min_dt.append(prices.iloc[i-window_range:i+window_range]['close'].idxmin())  
    maxima = pd.DataFrame(prices.loc[price_local_max_dt])
    minima = pd.DataFrame(prices.loc[price_local_min_dt])
    max_min = pd.concat([maxima, minima]).sort_index()
    print(max_min)
    max_min.index.name = 'date'
    max_min = max_min.reset_index()
    max_min = max_min[~max_min.index.duplicated()]
    p = prices.reset_index()   
    print(' p p date')
    l = len( p[p['date'].isin(max_min.date)].index.values)
    print(f''' l:{l} ''')
    print(f''' l1:{len(max_min)} ''')

    max_min['day_num'] = p[p['date'].isin(max_min.date)].index.values    
    # max_min = max_min.set_index('day_num')['close']
    
    return max_min


def plot_minmax_patterns(prices, max_min, patterns, stock, window, ema):
    prices = prices.set_index('timestamp',append = True)
    incr = str((prices.index[1] - prices.index[0]).seconds/60)
    
    if len(patterns) == 0:
        pass
    else:
        num_pat = len([x for x in patterns.items()][0][1])
        f, axes = plt.subplots(1, 2, figsize=(16, 5))
        axes = axes.flatten()
        prices_ = prices.reset_index()['close']
        axes[0].plot(prices_)
        axes[0].scatter(max_min.index, max_min, s=100, alpha=.3, color='orange')
        axes[1].plot(prices_)
        for name, end_day_nums in patterns.items():
            for i, tup in enumerate(end_day_nums):
                sd = tup[0]
                ed = tup[1]
                axes[1].scatter(max_min.loc[sd:ed].index,
                              max_min.loc[sd:ed].values,
                              s=200, alpha=.3)
                plt.yticks([])
        plt.tight_layout()
        plt.title('{}: {}: EMA {}, Window {} ({} patterns)'.format(stock, incr, ema, window, num_pat))

def get_results(prices, max_min, pat, stock, ema_, window_):
    
    incr = str((prices.index[1] - prices.index[0]).seconds/60)
    
    #fw_list = [1, 12, 24, 36] 
    fw_list = [1, 2, 3]
    results = []
    if len(pat.items()) > 0:
        end_dates = [v for k, v in pat.items()][0]      
        for date in end_dates:  
            param_res = {'stock': stock,
                         'increment': incr,
                         'ema': ema_,
                         'window': window_, 
                         'date': date}
            for x in fw_list:
                returns = (prices['close'].pct_change(x).shift(-x).reset_index(drop=True).dropna())
                try:
                    param_res['fw_ret_{}'.format(x)] = returns.loc[date[1]]   
                except Exception as e:
                    param_res['fw_ret_{}'.format(x)] = e
            results.append(param_res)  
    else:
        param_res = {'stock': stock,
                     'increment': incr,
                     'ema': ema_,
                     'window': window_,
                     'date': None}
        for x in fw_list:
            param_res['fw_ret_{}'.format(x)] = None   
        results.append(param_res)
    return pd.DataFrame(results)

def screener(stock_data, ema_list, window_list, plot, results):
    
    all_results = pd.DataFrame()
    
    for stock in [1]:
        prices = stock_data
        
        for ema_ in ema_list:
            for window_ in window_list: 
                max_min = get_max_min(prices, smoothing=ema_, window_range=window_)
                pat = find_patterns(max_min)
                
                if plot == True:
                    plot_minmax_patterns(prices, max_min, pat, stock, window_, ema_)
                    
                if results == True:
                    all_results = pd.concat([all_results, get_results(prices, max_min, pat, stock, ema_, window_)], axis=0)
                
    if results == True:
        return all_results.reset_index(drop=True)

if __name__ == '__main__':

    # Get data from database
    allMinutePriceData = model.getMinutePriceData(start = datetime(2020,11,25) ,
        end = datetime(2020,12,1),stockSymbol = 'INFY')    
    resampled_data = allMinutePriceData
    resampled_data = resampled_data.rename(columns={'datetime':'date'})
    resampled_data = resampled_data.set_index('date',append = True).dropna()
    ema_list = [3,10,20,30]
    window_list = [3,10,20,30]
    #results = screener(resampled_data, ema_list, window_list, plot =True, results = True)
    smoothing = 3
    window = 10

    minmax = get_max_min(resampled_data, smoothing, window)
    #print(minmax)