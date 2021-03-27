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

class Screener_SMA(bt.Analyzer):
    params = dict(period=10)

    def start(self):
        self.smas = {data: bt.indicators.SMA(data, period=self.p.period)
                     for data in self.datas}

    def stop(self):
        self.rets['over'] = list()
        self.rets['under'] = list()

        for data, sma in self.smas.items():
            node = data._name, data.close[0], sma[0]
            if data.close[0] > sma[0]:
                self.rets['over'].append(node)
            else:
                self.rets['under'].append(node)

if __name__ == '__main__':
    minutePriceData = model.getMinutePriceData(dayInterval = 5)
    UniqueSymbols = minutePriceData.symbol.unique().tolist()
    grouped = minutePriceData.groupby(minutePriceData.symbol)
    cerebro = bt.Cerebro()

    for symbol in UniqueSymbols :
        minutePriceData = grouped.get_group(symbol)
        minutePriceData = minutePriceData.set_index('datetime')        
        minutePriceData = bt.feeds.PandasData(
                dataname=minutePriceData)
        cerebro.adddata(minutePriceData,name=symbol)

    cerebro.addanalyzer(Screener_SMA, period=20)
    cerebro.run(runonce=False, stdstats=False, writer=True)
