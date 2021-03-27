from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from datetime import datetime as datetime  # For datetime objects
from datetime import time
import pandas as pd  # To manage paths
import sys  # To find out the script name (in argv[0])
import ta


# Import the backtrader platform
import backtrader as bt
import model
from indicators.VolumeWeightedAveragePrice import VolumeWeightedAveragePrice as vwap

# Create a Stratey
class VWAPMACDCO(bt.Strategy):
    sold = False
    sold_price = None
    stoploss = 1
    target = 2
    params = (
        # Standard MACD Parameters
        ('macd1', 12),
        ('macd2', 26),
        ('macdsig', 9)
    )
    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.vwap = vwap(self.data)
        self.add_timer(
                when=bt.timer.SESSION_START,
            )

        # self.macd = bt.indicators.MACD(self.data,
        #                                period_me1=self.p.macd1,
        #                                period_me2=self.p.macd2,
        #                                period_signal=self.p.macdsig)
        
        # self.mcross = bt.indicators.CrossOver( self.macd.signal,self.macd.macd)
        # self.mcross.plotinfo.plot = False

    def notify_timer(self, timer, when, *args, **kwargs):
            #print(f'''period is {self.vwap_period}''')            
            self.vwap_period = 1
            print('period is reset')

    def next(self):       
        self.vwap.vwap_period(self.vwap_period) 
        self.vwap_period += 1
        self.log(f'''Open:{self.data.open[0]}, High:{self.data.high[0]}, Low:{self.data.low[0]}, Close:{self.data.close[0]}, typprice:{self.vwap.typprice[0]}, cumtypprice:{self.vwap.cumtypprice[0]} , vwap:{self.vwap[0]}''')
        # if self.sold == False:
        #     if self.data.close[0] < self.data.open[0]:
        #         if (self.vwap[0] > self.data.close[0]
        #             and self.mcross[0] > 0.0):
        #             self.sold = True
        #             self.sell()
        #             self.sold_price = self.data.close[0]
        #             self.log(f''' sold @ Close:{self.data.close[0]} , vwap:{self.vwap[0]}''')
        #             return
        # if self.sold == True:

        #     if self.data.datetime.datetime(0).time() == time(15, 15):
        #         self.sell()
        #         self.log(f''' buy  @ market Close {self.data.close[0]},{self.sold_price}:{self.sold_price - self.data.close[0]}''')   
        #         self.sold = False
        #         return
        #     diff = (self.sold_price - self.data.close[0])
        #     diffpercent = (diff*100/self.sold_price)

        #     #buytrigger = ((self.vwap[0]) > self.data.close[0])
        #     buytrigger = False
        #     if diff > 0 and diffpercent > self.target:
        #         buytrigger = True
        #         self.log(f''' target reached {diffpercent}''')
        #     if diff < 0 and -diffpercent > self.stoploss:
        #         self.log(f''' stoploss triggered {-diffpercent} ''')
        #         buytrigger = True
                
        #     if buytrigger == True:
        #         self.buy()
        #         self.sold = False
        #         self.log('bought @ Close, %.2f' % self.data.close[0])

if __name__ == '__main__':

    # Get data from database
    allMinutePriceData = model.getMinutePriceData(start = datetime(2020,12,7) ,end = datetime(2020,12,17))       
    finalOutput = {}
    symbols = allMinutePriceData['symbol'].unique().tolist()
    symbols = ['BRITANNIA'] 
    #['ADANIPORTS','BAJAJ-AUTO','BAJAJFINSV','BAJFINANCE','BHARTIARTL','BRITANNIA','CIPLA','COALINDIA','DRREDDY','GAIL','GRASIM']
    for symbol in symbols:
        print(symbol)        
        minutePriceData = allMinutePriceData[allMinutePriceData['symbol'] == symbol]
        output = {}
        DFList = [group[1] for group in minutePriceData.groupby(minutePriceData['datetime'].dt.date)]        
        for df in DFList:  
            df = df.set_index('datetime')     
            # df = df.resample('5T', origin='start', closed='left', label='left').agg({'open': 'first',
            #                                                                     'high': 'max',
            #                                                                     'low': 'min',
            #                                                                     'close': 'last',
            #                                                                     'volume':'sum'}).dropna()                                                                 
            minutePriceData = bt.feeds.PandasData(
                dataname=df)
            cerebro = bt.Cerebro()
            # Add a strategy
            cerebro.addstrategy(VWAPMACDCO)
            # Add the Data Feeds to Cerebro
            cerebro.adddata(minutePriceData)
            # Set our desired cash start
            cerebro.broker.setcash(10000.0)

            cerebro.addsizer(bt.sizers.AllInSizerInt)
            # Print out the starting conditions
            startvalue =  cerebro.broker.getvalue()
            
            # Add TimeReturn Analyzers fot the annuyl returns   
            cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Days)
            
            results = cerebro.run()
            st0 = results[0]

            # for alyzer in st0.analyzers:
            #     alyzer.print()
                        
            endvalue =  cerebro.broker.getvalue()

            # Print out the final result
            output[df.index.date[0]] = ((endvalue-startvalue)*100/startvalue) 

        output = pd.Series(output)
        finalOutput[symbol] = output
    result = pd.DataFrame(finalOutput)

    print(result)
    print(result.sum())
    print(result.sum().mean())
    print(result.sum(axis =1))    
    print('Daily avg')
    print(result.sum(axis =1).mean())
    
    