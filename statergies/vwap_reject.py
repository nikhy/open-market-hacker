from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from datetime import datetime  # For datetime objects
import pandas as pd  # To manage paths
import sys  # To find out the script name (in argv[0])
import ta

# Import the backtrader platform
import backtrader as bt
import model
from indicators.supertrend import SuperTrend as SuperTrend
# Create a Stratey
class SuperTrendStat(bt.Strategy):
    bought = False
    first_bool = False
    bought_price = None
    second_bool = False
    stoploss = 18
    target = 30
    sl_hit = 0
    tg_hit = 0

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.vwap = vwap(period = 15 )
        
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

    def next(self):      
        if (self.bought == False 
                and self.first_bool == False
                and self.data.close[-1] > self.vwap[-1]
                and self.data.low[0] < self.vwap[0]):
            self.first_bool = True
            self.log(f''' first condition triggered on {self.data.datetime[0]} ''')
            return 
    
        if(self.first_bool == True and self.second_bool == False):
            if (self.data.close[0] >  self.vwap[0]):
                self.second_bool = True
                self.log(f''' second condition triggered on {self.data.datetime[0]} ''')
            else:
                self.first_bool = False
                self.log(f''' first condition negated on {self.data.datetime[0]} ''')
                
        
        if (self.bought == False 
                and self.first_bool == True
                and self.second_bool == True
                and self.data.open[0] < self.data.close[0]):
            self.bought = True
            self.buy()
            self.bought_price = self.data.close[0]
            self.log(f''' buy triggered on {self.data.close[0]} ''')
            return


        if (self.bought == True):
            if((self.data.close[0] >= (self.bought_price + self.target))):
                self.first_bool = False
                self.second_bool = False
                self.bought = False
                self.sell()
                self.tg_hit += 1
                self.log(' sell Close, %.2f' % self.data.close[0])
                return            
        if (self.bought == True and self.data.close[0] < (self.bought_price - self.stoploss) ):
            self.first_bool = False
            self.bought = False
            self.sell()
            self.sl_hit += 1            
            self.log(''' xxxxxxxxxxxx DANGER xxxxx ''')
            self.log(f''' sell  @ stoploss Close {self.data.close[0]},{self.bought_price}:{self.data.close[0] - self.bought_price}''')
    def notify_trade(self,trade):
        if not trade.isclosed:
            return
        dict_trade = {'price':trade.price, 'pnl' : trade.pnl}
        trades = pd.DataFrame(dict_trade,index =[0])   
        trades.to_csv('output/supertrend_1.csv', mode='a', header=False)
        
if __name__ == '__main__':

    # self.data.close[0] < self.data.open[0] or Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    # Get data from database
       

    output = {}
    allMinutePriceData = model.getMinutePriceData(start = datetime(2020,8,10) ,end = datetime(2020,12,25,0,0),
    stockSymbol = 'BANKNIFTY DEC FUT')    
    allMinutePriceData = allMinutePriceData.set_index('datetime')
    DFList = [group[1] for group in allMinutePriceData.groupby(allMinutePriceData['datetime'].dt.date)]        
    for df in DFList:  
        df = df.resample('5T', origin='start', closed='left', label='left').agg({'open': 'first',
                                                                            'high': 'max',
                                                                            'low': 'min',
                                                                            'close': 'last',
                                                                            'volume':'sum'}).dropna() 
        print(df.index.date[0])
        cerebro = bt.Cerebro()
        minutePriceData = bt.feeds.PandasData(
            dataname=df)
        # Add a strategy
        cerebro.addstrategy(SuperTrendStat)
        # Add the Data Feeds to Cerebro
        cerebro.adddata(minutePriceData)
        # Set our desired cash start
        cerebro.broker.setcash(745000.0)

        cerebro.addsizer(bt.sizers.AllInSizerInt)
        # Print out the starting conditions
        startvalue =  cerebro.broker.getvalue()
        
        #print('Starting Portfolio Value: %.2f' % startvalue)

        # Run over everything
        cerebro.run()

        # cerebro.plot(style='candle',volume = False)

        endvalue =  cerebro.broker.getvalue()
        # Print out the final result
        #print('Final Portfolio Value: %.2f' % endvalue)
        output[df.index.date[0]] = ((endvalue-startvalue)*100/startvalue) 

    output = pd.Series(output)
    #output.to_csv('output/supertrend.csv',header = ['P/L %'])    
    #print(output)
    print(output.mean())
    print(output.sum())
