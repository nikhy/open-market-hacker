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
    sold = False
    first_bool = False
    sold_price = None
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
        self.superTrend_1 = SuperTrend(period = 18,multiplier =3 )
        self.superTrend_2 = SuperTrend(period = 12,multiplier =2.5 )
        
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

    def next(self):      
        if (self.sold == False 
                and self.first_bool == False
                and self.data.close[-1] > self.superTrend_1.l.super_trend[-1]
                and self.data.close[-1] > self.superTrend_2.l.super_trend[-1]
                and self.data.close[0] < self.superTrend_1.l.super_trend[0]
                and self.data.close[0] < self.superTrend_2.l.super_trend[0]):
            self.first_bool = True
            self.log(f''' first condition triggered on {self.data.close[0]} ''')
            return 
    
        if(self.first_bool == True and self.second_bool == False):
            if (self.data.close[0] > self.superTrend_2.l.super_trend[0]):
                if(self.data.close[0] < self.superTrend_1.l.super_trend[0]):
                    self.second_bool = True
                    self.log(f''' second condition triggered on {self.data.close[0]} ''')
                    
                else:
                    self.first_bool = False
                return
        if (self.sold == False 
                and self.first_bool == True
                and self.second_bool == True
                and self.data.open[0] < self.data.close[0]):
            self.sold = True
            self.sell()
            self.sold_price = self.data.close[0]
            self.log(f''' sell triggered on {self.data.close[0]} ''')
            return


        if (self.sold == True):
            if((self.data.close[0] <= (self.sold_price - self.target))):
                self.first_bool = False
                self.second_bool = False
                self.sold = False
                self.buy()
                self.tg_hit += 1
                self.log(' buy Close, %.2f' % self.data.close[0])
                return            
        if (self.sold == True and self.data.close[0] > (self.sold_price + self.stoploss) ):
            self.first_bool = False
            self.sold = False
            self.buy()
            self.sl_hit += 1            
            self.log(''' xxxxxxxxxxxx DANGER xxxxx ''')
            self.log(f''' buy  @ stoploss Close {self.data.close[0]} - {self.sold_price}''')
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
    allMinutePriceData = model.getMinutePriceData(start = datetime(2020,6,10) ,end = datetime(2020,12,24,0,0),
    stockSymbol = 'BANKNIFTY DEC FUT')    
    DFList = [group[1] for group in allMinutePriceData.groupby(allMinutePriceData['datetime'].dt.date)]        
    for df in DFList:  
        df = df.set_index('datetime')
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