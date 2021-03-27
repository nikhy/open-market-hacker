from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import pandas as pd  # To manage paths
import sys  # To find out the script name (in argv[0])
import ta


# Import the backtrader platform
import backtrader as bt
import model
from indicators.VolumeWeightedAveragePrice import VolumeWeightedAveragePrice as vwap
from indicators.StochRSI import StochasticRSI as StochRSI

# Create a Stratey
class EngulfingPtrnStrategy(bt.Strategy):
    bought = False
    bought_price = None
    stoploss = 0.5
    target = 1
    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.vwap = vwap(period = 15 )
        self.StochRSI = StochRSI()
        

    def next(self):       
        if self.bought == False:
            if self.data.close[0] > self.data.open[0]:
                if (self.vwap[-2] > self.data.close[-2] 
                    and self.vwap[-1] < self.data.close[-1] 
                    and self.vwap[0] < self.data.close[0]):
        
                    self.bought = True
                    self.buy()
                    self.bought_price = self.data.close[0]
                    self.log('bought @ Close, %.2f' % self.data.close[0])
                    return
        if self.bought == True:
            vwapfalling = self.vwap[-1] > self.vwap[0]             
            selltrigger = ((self.vwap[0]) > self.data.close[0]) or vwapfalling
            diff = self.data.close[0] - self.bought_price
            diffpercent = -(diff*100/self.bought_price)
            print(f'''diffpercent {diffpercent}''')
            if diff < 0 and diffpercent > self.stoploss:
                print(f''' stoploss triggered {diff} ''')
                selltrigger = True
            if selltrigger == True:
                self.sell()
                self.bought = False
                self.log('sold @ Close, %.2f' % self.data.close[0])


if __name__ == '__main__':

    # self.data.close[0] < self.data.open[0] or Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    # Get data from database
    minutePriceData = model.getMinutePriceData(dayInterval = 10)
    #priceData = model.getMinutePriceData(dayInterval = 3)

    #priceData = priceData[priceData['symbol'] == 'INFY']
    minutePriceData = minutePriceData[minutePriceData['symbol'] == 'AXISBANK']
    
    minutePriceData = minutePriceData.set_index('datetime')
    # priceData = priceData.set_index('datetime')
    # Create a Data Feeds
    # priceData = bt.feeds.PandasData(dataname=priceData)
    

    DFList = [group[1] for group in minutePriceData.groupby(minutePriceData.index.date)]
    output = []
    for df in DFList:
        print(df.index.date[0])
        cerebro = bt.Cerebro()
        minutePriceData = bt.feeds.PandasData(
            dataname=df)
        # Add a strategy
        cerebro.addstrategy(EngulfingPtrnStrategy)
        # Add the Data Feeds to Cerebro
        #cerebro.adddata(priceData)
        #cerebro.resampledata(minutePriceData,timeframe = bt.TimeFrame.Minutes,compression = 5)
        cerebro.adddata(minutePriceData)
        # Set our desired cash start
        cerebro.broker.setcash(10000.0)

        cerebro.addsizer(bt.sizers.AllInSizerInt)
        # Print out the starting conditions
        startvalue =  cerebro.broker.getvalue()
        print('Starting Portfolio Value: %.2f' % startvalue)

        # Run over everything
        cerebro.run()
        cerebro.plot(style='candle',volume = False)

        endvalue =  cerebro.broker.getvalue()
        # Print out the final result
        print('Final Portfolio Value: %.2f' % endvalue)
        output.append((endvalue-startvalue)*100/startvalue) 
        break

    output = pd.Series(output)
    print(output.sort_values())
    print(output.sum())