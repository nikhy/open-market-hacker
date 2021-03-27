from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from datetime import datetime as datetime  # For datetime objects
import pandas as pd  # To manage paths
import sys  # To find out the script name (in argv[0])
import ta
from market_profile import MarketProfile

# Import the backtrader platform
import backtrader as bt
import model
from indicators.VolumeWeightedAveragePrice import VolumeWeightedAveragePrice as vwap

class TheStrategy(bt.Strategy):
    bought = False
    bought_price = None
    stoploss = 0.5
    target = .75
    '''
    This strategy is loosely based on some of the examples from the Van
    K. Tharp book: *Trade Your Way To Financial Freedom*. The logic:

      - Enter the market if:
        - The MACD.macd line crosses the MACD.signal line to the upside
        - The Simple Moving Average has a negative direction in the last x
          periods (actual value below value x periods ago)

     - Set a stop price x times the ATR value away from the close

     - If in the market:

       - Check if the current close has gone below the stop price. If yes,
         exit.
       - If not, update the stop price if the new stop price would be higher
         than the current
    '''

    params = (
        # Standard MACD Parameters
        ('macd1', 12),
        ('macd2', 26),
        ('macdsig', 9),
        ('atrperiod', 14),  # ATR Period (standard)
        ('atrdist', 3.0),   # ATR distance for stop price
        ('smaperiod', 30),  # SMA Period (pretty standard)
        ('dirperiod', 10),  # Lookback period to consider SMA trend direction
    )

    def notify_order(self, order):
        if order.status == order.Completed:
            pass

        if not order.alive():
            self.order = None  # indicate no order is pending

    def __init__(self):
        self.macd = bt.indicators.MACD(self.data,
                                       period_me1=self.p.macd1,
                                       period_me2=self.p.macd2,
                                       period_signal=self.p.macdsig)
        
        # VWAP 
        self.vwap = vwap(period = 10 )

        # Cross of macd.macd and macd.signal
        self.mcross = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)
        # To set the stop price
        self.atr = bt.indicators.ATR(self.data, period=self.p.atrperiod)


    def start(self):
        self.order = None  # sentinel to avoid operrations on pending order

    def next(self):
        if self.order:
            return  # pending order execution

        if not self.position:  # not in the market
            print('checking')
            if (self.vwap[-2] > self.data.close[-2] 
                and self.vwap[-1] < self.data.close[-1]
                and self.mcross[0] > 0.0):
                self.order = self.buy()
                pdist = self.atr[0] * self.p.atrdist
                self.pstop = self.data.close[0] - pdist

        else:  # in the market
            pclose = self.data.close[0]
            pstop = self.pstop

            if pclose < pstop:
                self.close()  # stop met - get out
            else:
                pdist = self.atr[0] * self.p.atrdist
                # Update only if greater than
                self.pstop = max(pstop, pclose - pdist)


# Create a Stratey
class VWAPMACDCO(bt.Strategy):
    bought = False
    bought_price = None
    stoploss = 0.5
    target = 1
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
        self.vwap = vwap(period = 10 )
        self.macd = bt.indicators.MACD(self.data,
                                       period_me1=self.p.macd1,
                                       period_me2=self.p.macd2,
                                       period_signal=self.p.macdsig)
        
        self.mcross = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)
        self.mcross.plotinfo.plot = False
    
    def next(self):       
        if self.bought == False:
            if self.data.close[0] > self.data.open[0]:
                if (self.vwap[0] < self.data.close[0]
                    and self.mcross[0] > 0.0):
                    self.bought = True
                    self.buy()
                    self.bought_price = self.data.close[0]
                    self.log('bought @ Close, %.2f' % self.data.close[0])
                    return
        if self.bought == True:
            diff = self.data.close[0] - self.bought_price
            diffpercent = (diff*100/self.bought_price)

            #selltrigger = ((self.vwap[0]) > self.data.close[0])
            selltrigger = False
            if diff > 0 and diffpercent > self.target:
                selltrigger = True
                self.log(''' target reached ''')
            if diff < 0 and diffpercent < -self.stoploss:
                self.log(f''' stoploss triggered {diff} ''')
                selltrigger = True
                
            if selltrigger == True:
                self.sell()
                self.bought = False
                self.log('sold @ Close, %.2f' % self.data.close[0])

if __name__ == '__main__':

    # Get data from database
    allMinutePriceData = model.getMinutePriceData(start = datetime(2020,12,31) ,end = datetime(2021,1,1))       
    finalOutput = {}
    symbols = allMinutePriceData['symbol'].unique().tolist()
    for symbol in symbols:
        print(symbol)        
        minutePriceData = allMinutePriceData[allMinutePriceData['symbol'] == symbol]
        minutePriceData = minutePriceData.set_index('datetime')    
        output = {}
        DFList = [group[1] for group in minutePriceData.groupby(minutePriceData.index.date)]        
        for df in DFList:
            cerebro = bt.Cerebro()
            print(df.index.date[0])
            print('starting resampling..')
            df = df.resample('3T', origin='start', closed='left', label='left').agg({'open': 'first',
                                                                            'high': 'max',
                                                                            'low': 'min',
                                                                            'close': 'last',
                                                                            'volume':'sum'}).dropna()  
            df = df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'})
            print('stopping resampling..')  
            mp = MarketProfile(df)  
            mp_slice = mp[df.index.min():df.index.max()]
            print(mp_slice.profile)
            break
            minutePriceData = bt.feeds.PandasData(
                dataname=df)
            # Add a strategy
            cerebro.addstrategy(VWAPMACDCO)
            # Add the Data Feeds to Cerebro
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
            output[df.index.date[0]] = ((endvalue-startvalue)*100/startvalue) 
            #break

        output = pd.Series(output)
        finalOutput[symbol] = output
        break
    result = pd.DataFrame(finalOutput)

    print(result)
    print(result.sum())
    print(result.sum().mean())
    print(result.sum(axis =1))    
    print('Daily avg')
    print(result.sum(axis =1).mean())
    
    