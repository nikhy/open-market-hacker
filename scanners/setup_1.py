from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from datetime import datetime  # For datetime objects
from datetime import time  # For datetime objects

import pandas as pd 


# Import the backtrader platform
import backtrader as bt
import model

class Screener_SMA(bt.Analyzer):
    params = dict(period=10)

    def start(self):
        self.smas200 = {data: bt.indicators.SMA(data, period=200)
                     for data in self.datas}
        self.smas20 = {data: bt.indicators.SMA(data, period=20)
                     for data in self.datas}
        self.rsi = {data: bt.indicators.RSI(data, period=14,upperband = 60,safediv = True)
                     for data in self.datas}

    def stop(self):
        self.rets['over'] = list()
        self.rets['under'] = list()

        for data in self.datas:
            node = data._name, data.close[0]
            if self.smas20[data][0] > self.smas200[data][0] and self.rsi[data][0] > 60:
                self.rets['over'].append(node)
    def get_analysis(self):
        return self.rets

def Setup1Scanner():
    minutePriceData = model.getNifty50MinutePriceData(start = datetime(2021,1,5) ,end = datetime.now())       
    UniqueSymbols = minutePriceData.symbol.unique().tolist()
    grouped = minutePriceData.groupby(minutePriceData.symbol)
    cerebro = bt.Cerebro()

    for symbol in UniqueSymbols :
        minutePriceData = grouped.get_group(symbol)
        minutePriceData = minutePriceData.set_index('datetime')        
        
        minutePriceData = minutePriceData.resample('5T', origin='start', closed='left', label='left').agg({'open': 'first',
                                                                        'high': 'max',
                                                                        'low': 'min',
                                                                        'close': 'last',
                                                                        'volume':'sum'}).dropna()  
        minutePriceData = bt.feeds.PandasData(
                dataname=minutePriceData)
        cerebro.adddata(minutePriceData,name=symbol)

    cerebro.addanalyzer(Screener_SMA, period=20)
    print(f''' start running ''')
    out = cerebro.run(runonce=False, stdstats=False, writer=False)
    return (out[0].analyzers[0].get_analysis())
