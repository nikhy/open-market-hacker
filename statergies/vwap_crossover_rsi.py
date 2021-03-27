from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from datetime import datetime as datetime  # For datetime objects
import pandas as pd  # To manage paths
import sys  # To find out the script name (in argv[0])
import ta


# Import the backtrader platform
import backtrader as bt
import model
from indicators.VolumeWeightedAveragePrice import VolumeWeightedAveragePrice as vwap
from indicators.StochRSI import StochasticRSI as StochRSI

# Create a Stratey
class VWAPRSICO(bt.Strategy):
    bought = False
    bought_price = None
    stoploss = 0.5
    target = .75
    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        #print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.vwap = vwap(period = 10 )
        self.StochRSI = StochRSI()
        

    def next(self):       
        if self.bought == False:
            if self.data.close[0] > self.data.open[0]:
                if (self.vwap[-2] > self.data.close[-2] 
                    and self.vwap[-1] < self.data.close[-1]
                    and self.StochRSI.l.fastk > self.StochRSI.l.fastd
                ):
                    self.bought = True
                    self.buy()
                    self.bought_price = self.data.close[0]
                    self.log('bought @ Close, %.2f' % self.data.close[0])
                    return
        if self.bought == True:
            diff = self.data.close[0] - self.bought_price
            diffpercent = (diff*100/self.bought_price)
            self.log(f'''diffpercent {diffpercent}''')

            selltrigger = ((self.vwap[0]) > self.data.close[0])
            #selltrigger = ((self.data.close[0]) < self.data.low[-1])
            
            if diff > 0 and diffpercent > self.target:
                self.log(f''' target triggered {diff} ''')
                selltrigger = True
            if diff < 0 and diffpercent < -self.stoploss:
                self.log(f''' stoploss triggered {diff} ''')
                selltrigger = True
            if selltrigger == True:
                self.sell()
                self.bought = False
                self.log('sold @ Close, %.2f' % self.data.close[0])

        self.log(f'''xxx Close: {self.data.close[0]} ,Volume {self.data.volume[0]}''')



if __name__ == '__main__':

    # Get data from database
    allMinutePriceData = model.getMinutePriceData(start = datetime(2020,8,1) ,end = datetime(2020,12,1),
    stockSymbol = 'BANKNIFTY20DECFUT')       
    finalOutput = {}
    symbols = allMinutePriceData['symbol'].unique().tolist()
    for symbol in symbols:
        #print(symbol)        
        minutePriceData = allMinutePriceData[allMinutePriceData['symbol'] == symbol]
        minutePriceData = minutePriceData.set_index('datetime')    
        output = {}
        DFList = [group[1] for group in minutePriceData.groupby(minutePriceData.index.date)]        
        for df in DFList:
            cerebro = bt.Cerebro()
            print(df.index.date[0])
            print('starting resampling..')
            df = df.resample('5T', origin='start', closed='left', label='left').agg({'open': 'first',
                                                                            'high': 'max',
                                                                            'low': 'min',
                                                                            'close': 'last',
                                                                            'volume':'sum'}).dropna()  
            print('stopping resampling..')    
            minutePriceData = bt.feeds.PandasData(
                dataname=df)
            # Add a strategy
            cerebro.addstrategy(VWAPRSICO)
            # Add the Data Feeds to Cerebro
            cerebro.adddata(minutePriceData)
            # Set our desired cash start
            cerebro.broker.setcash(10000.0)

            #cerebro.addsizer(bt.sizers.AllInSizerInt)
            # Print out the starting conditions
            startvalue =  cerebro.broker.getvalue()
            print('Starting Portfolio Value: %.2f' % startvalue)

            # Run over everything
            cerebro.run()
            #cerebro.plot(style='candle',volume = False)

            endvalue =  cerebro.broker.getvalue()
            # Print out the final result
            print('Final Portfolio Value: %.2f' % endvalue)
            output[df.index.date[0]] = ((endvalue-startvalue)*100/startvalue) 
            #break

        output = pd.Series(output)
        finalOutput[symbol] = output
    result = pd.DataFrame(finalOutput)

    print(result)
    print(result.sum())
    print(result.sum().mean())
    print(result.sum(axis =1))    
    print('Daily avg')
    print(result.sum(axis =1).mean())
    
    