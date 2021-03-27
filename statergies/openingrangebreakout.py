from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from datetime import datetime 
from datetime import time # For datetime objects
import pandas as pd  # To manage paths
import sys  # To find out the script name (in argv[0])
import ta

# Import the backtrader platform
import backtrader as bt
import model
from indicators.supertrend import SuperTrend as SuperTrend
# Create a Stratey
class ORB(bt.Strategy):
    opening_low = None
    opening_high = 0
    opening_range = 0
    bought = False
    already_traded = False
    bought_price = None
    stoploss = 0
    target = 0
    sl_hit = 0
    tg_hit = 0
    c = 0.75

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        #print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

    def get_target(self):
        return self.bought_price +(self.opening_range) + (self.bought_price * self.c/100) 
    def get_stoploss(self):
        return self.opening_low +(self.opening_range/2)

    def next(self):  
        if(self.datas[0].datetime.datetime(0).time() <= time(9, 30)):        
            if self.datas[0].datetime.datetime(0).time() == time(9, 15):  
                self.opening_low = self.data.low[0]      
                self.opening_open = self.data.open[0]   
                self.opening_high = self.data.high[0]
                   
            if (self.opening_high < self.data.high[0]):                        
                    self.opening_high = self.data.high[0]
                    self.opening_range = (self.opening_high - self.opening_low)  
            if (self.opening_low > self.data.low[0]):                        
                    self.opening_low = self.data.low[0]
                    self.opening_range = (self.opening_high - self.opening_low) 
            self.opening_close = self.data.close[0]       
            return
        if (self.opening_open != self.opening_low):    
            return                    

        if (self.bought == False 
                and self.opening_high < self.data.close[0]
                and self.already_traded != True):
            self.bought = True
            self.buy()
            self.bought_price = self.data.close[0]
            self.log(f''' buy triggered on {self.data.close[0]} ''')
            return

        if (self.bought == True and self.already_traded != True ):
            if self.datas[0].datetime.datetime(0).time() == time(15, 17):
                self.sell()
                self.log(f''' sell  @ market Close {self.data.close[0]},{self.bought_price}:{self.data.close[0] - self.bought_price}''')
                
            if(self.data.close[0] >= self.get_target()):
                self.bought = False
                self.sell()
                self.tg_hit += 1
                self.already_traded = True
                self.log(' sell Close, %.2f' % self.data.close[0])
                return            
        if (self.bought == True and self.data.close[0] < self.get_stoploss() ):
            self.bought = False
            self.sell()
            self.already_traded = True            
            self.sl_hit += 1            
            self.log(''' xxxxxxxxxxxx DANGER xxxxx ''')
            self.log(f''' sell  @ stoploss Close {self.data.close[0]},{self.bought_price}:{self.data.close[0] - self.bought_price}''')

if __name__ == '__main__':

    # self.data.close[0] < self.data.open[0] or Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    # Get data from database
       

    output = {}
    allMinutePriceData = model.getMinutePriceData(start = datetime(2020,12,1) ,end = datetime(2020,12,25,0,0)) 
    finalOutput = {}   
    symbols = allMinutePriceData['symbol'].unique().tolist()
    symbols = ['ADANIPORTS','ASIANPAINT','AXISBANK','BAJAJ-AUTO','BAJAJFINSV','BAJFINANCE','BHARTIARTL','BPCL','BRITANNIA','CIPLA','COALINDIA','DRREDDY','EICHERMOT','GAIL','GRASIM','HCLTECH','HDFC','HDFCBANK','HEROMOTOCO','HINDALCO','HINDUNILVR','ICICIBANK','INDUSINDBK','INFRATEL','INFY','IOC','ITC','JSWSTEEL','KOTAKBANK','LT','M&M','MARUTI','NESTLEIND','NTPC','ONGC','POWERGRID','RELIANCE','SBIN','SHREECEM','SUNPHARMA','TATAMOTORS','TATASTEEL','TCS','TECHM','TITAN','ULTRACEMCO','UPL','VEDL','WIPRO','ZEEL']
    print(symbols)
    for symbol in symbols:
        minutePriceData = allMinutePriceData[allMinutePriceData['symbol'] == symbol]
        minutePriceData = minutePriceData.set_index('datetime')    
        if(minutePriceData['close'].mean() < 100 ):
            print(f''' breaking {symbol}  {minutePriceData['close'].mean()}''')
            continue
        output = {}
        DFList = [group[1] for group in minutePriceData.groupby(minutePriceData.index.date)] 
        for df in DFList:  
            cerebro = bt.Cerebro()
            minutePriceData = bt.feeds.PandasData(
                dataname=df)
            # Add a strategy
            cerebro.addstrategy(ORB)
            # Add the Data Feeds to Cerebro
            cerebro.adddata(minutePriceData)
            # Set our desired cash start
            cerebro.broker.setcash(800000.0)

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
        finalOutput[symbol] = output
    
    result = pd.DataFrame(finalOutput)
    result.sum(axis =1).to_csv('ORB_all_sum_dec.csv')  
    result.to_csv('ORB_all_dec.csv')
    print(result.sum(axis =1).mean())