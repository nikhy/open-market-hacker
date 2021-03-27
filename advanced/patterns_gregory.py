
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
def find_trough(x):  
    x = x.reset_index(drop=True)
    return len(x) == 3 and x[0] > x[1] and x[2] > x[1]

def find_peek(x):  
    x = x.reset_index(drop=True)
    return len(x) == 3 and x[0] < x[1] and x[2] < x[1]

if __name__ == '__main__':

    # Get data from database
    hist = model.getMinutePriceData(start = datetime(2020,11,1) ,
        end = datetime(2020,12,1),stockSymbol = 'INFY')    
    hist = hist.resample('5T', origin='start', closed='left', label='left').agg({'open': 'first',
                                                                                'high': 'max',
                                                                                'low': 'min',
                                                                                'close': 'last',
                                                                                'volume':'sum'}).dropna()           
    # x = np.flatnonzero(hist.close.rolling(window=3, min_periods=1, center=True).aggregate(find_trough).tolist())
    # minimaIdxs = [hist.index.get_loc(y) for y in x[x == 1]]
    # x = np.flatnonzero(hist.close.rolling(window=3, min_periods=1, center=True).aggregate(find_peek).tolist())
    # maximaIdxs = [hist.index.get_loc(y) for y in x[x == 1]]
    hs = hist.close.loc[hist.close.shift(-1) != hist.close]
    x = hs.rolling(window=3, center=True).aggregate(find_trough)
    minimaIdxs = [hist.index.get_loc(y) for y in x[x == 1].index]
    x = hs.rolling(window=3, center=True).aggregate(find_peek)
    maximaIdxs = [hist.index.get_loc(y) for y in x[x == 1].index]
    print(minimaIdxs)
    print(maximaIdxs)
