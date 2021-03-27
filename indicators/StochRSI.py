from backtrader.indicators import Indicator, MovAv, RelativeStrengthIndex, Highest, Lowest
import backtrader as bt
from backtrader import  DivByZero

class StochasticRSI(Indicator):
      """
      K - The time period to be used in calculating the %K. 3 is the default.
      D - The time period to be used in calculating the %D. 3 is the default.
      RSI Length - The time period to be used in calculating the RSI
      Stochastic Length - The time period to be used in calculating the Stochastic
  
      Formula:
      %K = SMA(100 * (RSI(n) - RSI Lowest Low(n)) / (RSI HighestHigh(n) - RSI LowestLow(n)), smoothK)
      %D = SMA(%K, periodD)
  
      """
      lines = ('fastk', 'fastd',)
  
      params = (
          ('k_period', 3),
          ('d_period', 3),
          ('rsi_period', 14),
          ('stoch_period', 14),
          ('movav', MovAv.Simple),
          ('rsi', RelativeStrengthIndex),
          ('upperband', 80.0),
          ('lowerband', 20.0),
      )
  
      plotlines = dict(percD=dict(_name='%D', ls='--'),
                       percK=dict(_name='%K'))
  
      def _plotlabel(self):
        plabels = [self.p.k_period, self.p.d_period, self.p.rsi_period, self.p.stoch_period]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels

      def _plotinit(self):
        self.plotinfo.plotyhlines = [self.p.upperband, self.p.lowerband]
  
      def __init__(self):
        rsi = bt.ind.RSI_Safe(period=self.p.rsi_period)
        rsi_ll = bt.ind.Lowest(rsi, period=self.p.rsi_period)
        rsi_hh = bt.ind.Highest(rsi, period=self.p.rsi_period)
        stochrsi = DivByZero((rsi - rsi_ll),(rsi_hh - rsi_ll),zero=True)
        #stochrsi = (rsi - rsi_ll)/(rsi_hh - rsi_ll)  
        self.l.fastk = k = self.p.movav(100.0 * stochrsi, period=self.p.k_period)
        self.l.fastd = self.p.movav(k, period=self.p.d_period)