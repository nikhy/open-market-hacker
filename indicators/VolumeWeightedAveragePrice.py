
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import datetime  # For datetime objects
import pandas as pd  # for reading data
import backtrader as bt
import backtrader.indicators as btind

class vwap(bt.Indicator):

    ''' This indicator needs a timer to reset the period to 1 at every session start
        also it needs a flag in next section of strategy to increment the self._vwap_period 
        run cerebro with runonce=False as we need dynamic indicator'''

    plotinfo = dict(subplot=False)

    alias = ('VWAP', 'VolumeWeightedAveragePrice','vwap',)
    lines = ('VWAP','typprice','cumprice', 'cumtypprice',)
    plotlines = dict(VWAP=dict(alpha=1.0, linestyle='-', linewidth=2.0, color = 'magenta'))

    def __init__(self):
        self._vwap_period = 1
        
    def vwap_period(self, period):
        self._vwap_period = period
        

    def next(self):
        
        self.l.typprice[0] = ((self.data.close + self.data.high + self.data.low)/3) * self.data.volume
        self.l.cumtypprice[0] = sum(self.l.typprice.get(size=self._vwap_period), self._vwap_period)
        self.cumvol = sum(self.data.volume.get(size=self._vwap_period), self._vwap_period)
        self.lines.VWAP[0] = self.l.cumtypprice[0] / self.cumvol

        #super(vwap, self).__init__()