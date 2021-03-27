// This source code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
// © nikhy
//@version=4
strategy("MACD_VWAP_CO_Strategy", overlay=true)
strategy.risk.max_intraday_filled_orders(count = 2)
fast = 12, slow = 26
fastMA = ema(close, fast)
slowMA = ema(close, slow)
macd = fastMA - slowMA
signal = sma(macd, 9)
vwapval =  vwap(hlc3)
plot(vwapval, color=color.blue)
vwapcond = (vwapval < close+3)
longCondition = ((macd - signal) > 0 and macd > 0)
if (vwapcond and longCondition )
    strategy.entry("My Long Entry Id", strategy.long)

longExitPrice  = strategy.position_avg_price * (1 + 0.005)
longStopPrice  = strategy.position_avg_price * (1 - 0.003)

// Plot take profit values for confirmation
plot(series=(strategy.position_size > 0) ? longExitPrice : na,
     color=color.green,
     linewidth=3, title="Long Take Profit")
     
plot(series=(strategy.position_size > 0) ? longStopPrice : na,
     color=color.blue,
     linewidth=3, title="Long Stop Profit")

if (strategy.position_size > 0)
    strategy.exit(id="exit", limit=longExitPrice , stop=longStopPrice)
