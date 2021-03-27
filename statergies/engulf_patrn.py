from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import pandas as pd  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt
import model


# Create a Stratey
class EngulfingPtrnStrategy(bt.Strategy):
    bought = False
    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.engulfing = bt.talib.CDLENGULFING(self.data.open, self.data.high,
                             self.data.low, self.data.close)
        self.ema = bt.indicators.MovingAverageExponential(self.data.close , period = 50)


    def next(self):        
        if self.bought == True:
            print('stock sold at Close, %.2f' % self.data.close[0])
            self.sell()
            self.bought = False
        res = (self.engulfing[0] == 100) and self.ema[0] < self.data.close[0] 
        if res == True:
            self.bought = True
            print('stock bought  at Close, %.2f' % self.data.close[0])
            self.buy()
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.data.close[0])


if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(EngulfingPtrnStrategy)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    # Get data from database
    priceData = model.getPriceData(dayInterval = 800)
    priceData = priceData[priceData['symbol'] == 'INFY']
    priceData = priceData.set_index('datetime')
    # Create a Data Feed
    data = bt.feeds.PandasData(
        dataname=priceData)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()
    cerebro.plot()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
