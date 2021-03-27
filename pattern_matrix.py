import model
import talib
import pandas as pd
from datetime import date,timedelta

from candlestick_patterns import candlestick_patterns 
def prev_weekday(adate):
    return date.today()
    _offsets = (3, 1, 1, 1, 1, 1, 2)
    return adate - timedelta(days=_offsets[adate.weekday()])
def pattern_matrix(dayRange):
    res_dict = {}
    global candlestick_patterns
    full_price_data = model.getPriceData(dayRange)
    full_price_data = full_price_data.set_index('timestamp')
    stocks = full_price_data['symbol'].drop_duplicates()
    for stock_name in stocks:
        for pattern_key in candlestick_patterns:
            pattern_function = getattr(talib, pattern_key)                   
            price_data = full_price_data.loc[full_price_data['symbol'] == stock_name]
            results = pattern_function(price_data['open'], price_data['high'], price_data['low'], price_data['close'])
            for  timestamp,score in results.iteritems():
                if score != 0: 
                    score = float(score)
                    if stock_name not in res_dict:
                        res_dict[stock_name] = {
                            'total':0,
                            'bear_total':0,
                            'bull_total':0,
                            'patterns':[]
                        }
                    res_dict[stock_name]['is_today'] = prev_weekday(date.today()) == timestamp
                    pattern_dict = {
                        'name':candlestick_patterns[pattern_key],
                        'timestamp':timestamp,
                        'score':score
                    }
                    res_dict[stock_name]['patterns'].append(pattern_dict)
                    res_dict[stock_name]['total'] += score
                    if score > 0:
                        res_dict[stock_name]['bull_total'] += score
                    else:
                        res_dict[stock_name]['bear_total'] += score 
    res_df = pd.DataFrame(res_dict).transpose()
    #res_df = res_df.loc[res_df['is_today'] == True]
    bearish_stocks=res_df.loc[res_df['total']<100] \
        .sort_values(by='total',ascending=True) \
        .transpose().to_dict()
    bullish_stocks=res_df.loc[res_df['total']>100] \
        .sort_values(by='total',ascending=True)    \
        .transpose().to_dict()    
    res ={
         'bearish_stocks':bearish_stocks,
         'bullish_stocks':bullish_stocks  
    }
    return res
