from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from datetime import datetime  # For datetime objects
import pandas as pd  # To manage paths
import sys  # To find out the script name (in argv[0])
import ta

# Import the backtrader platform
import backtrader as bt
import model
from indicators.VolumeWeightedAveragePrice import VolumeWeightedAveragePrice as vwap
from indicators.StochRSI import StochasticRSI as StochRSI

# Create a Stratey
class SMA200(bt.Strategy):
    bought = False
    bought_price = None
    stoploss = 0.5
    target = 1
    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        #print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.sma =  bt.ind.SimpleMovingAverage(self.data.close,period =200)

    def next(self):      
        if  self.bought == False and self.data.close[0] > self.sma[0]:
            self.bought = True
            self.buy()
            self.log('buy @ Close, %.2f' % self.data.close[0])
        elif  self.bought == True and self.data.close[0] < self.sma[0]:
            self.sell()
            self.bought = False
            self.log('sold @ Close, %.2f' % self.data.close[0])

if __name__ == '__main__':

    # self.data.close[0] < self.data.open[0] or Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    # Get data from database
       

    output = {}
    allMinutePriceData = model.getMinutePriceData(start = datetime(2018,1,1) ,end = datetime(2020,12,1))    
    symbols = allMinutePriceData['symbol'].unique().tolist()
    for symbol in symbols:
        df = allMinutePriceData[allMinutePriceData['symbol'] == symbol]
        df = df.set_index('datetime')
        cerebro = bt.Cerebro()
        df = df.resample('60T', origin='start', closed='left', label='left').agg({'open': 'first',
                                                                            'high': 'max',
                                                                            'low': 'min',
                                                                            'close': 'last',
                                                                            'volume':'sum'}).dropna()
        minutePriceData = bt.feeds.PandasData(
            dataname=df)
        # Add a strategy
        cerebro.addstrategy(SMA200)
        # Add the Data Feeds to Cerebro
        cerebro.adddata(minutePriceData)
        # Set our desired cash start
        cerebro.broker.setcash(10000.0)

        cerebro.addsizer(bt.sizers.AllInSizerInt)
        # Print out the starting conditions
        startvalue =  cerebro.broker.getvalue()
        #print('Starting Portfolio Value: %.2f' % startvalue)

        # Run over everything
        cerebro.run()
        cerebro.plot(style='candle',volume = False)

        endvalue =  cerebro.broker.getvalue()
        # Print out the final result
        #print('Final Portfolio Value: %.2f' % endvalue)
        output[symbol] = ((endvalue-startvalue)*100/startvalue) 
   
    output = pd.Series(output)
    output.to_csv('output/sma200_2018_to_2020dec.csv',header = ['P/L %'])    
    print(output.sort_values())
    print(output.mean())