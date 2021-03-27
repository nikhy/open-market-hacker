'''
Author: B. Bradford 

MIT License

Copyright (c) B. Bradford

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

That they contact me for shipping information for the purpose of sending a 
local delicacy of their choice native to whatever region they are domiciled.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
import backtrader as bt

class VolumeWeightedAveragePrice(bt.Indicator):
    plotinfo = dict(subplot=False)

    params = (('period', 30), )

    alias = ('VWAP', 'VolumeWeightedAveragePrice',)
    lines = ('VWAP',)
    plotlines = dict(VWAP=dict(alpha=0.50, linestyle='-.', linewidth=2.0))



    def __init__(self):
        # Before super to ensure mixins (right-hand side in subclassing)
        # can see the assignment operation and operate on the line
        cumvol = bt.ind.SumN(self.data.volume, period = self.p.period)
        typprice = ((self.data.close + self.data.high + self.data.low)/3) * self.data.volume
        cumtypprice = bt.ind.SumN(typprice, period=self.p.period)
        self.lines[0] = cumtypprice / cumvol

        super(VolumeWeightedAveragePrice, self).__init__()
