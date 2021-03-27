from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options

import json
import time 
import pandas as pd
from config import config
from datetime import datetime

tv_config = config(filename='tv.ini',section='tv')



def day_zone_scanner_zerodha(kite = None, buffer = 0.005):
    output = { 'bearish':[] , 'bullish':[] }
    try:
        day_zones = pd.read_csv('data/day_zones.csv')
        day_zones['full_symbol'] = (day_zones['symbol'].map('NSE:{}'.format))
        intruments = day_zones['full_symbol'].array
        price_data = kite.quote(intruments)
        price_dict = dict((key,price_data[key]['last_price'])for key in price_data)
        for index, row in day_zones.iterrows(): 
            full_symbol = row["full_symbol"]
            symbol = row["symbol"]
            price = price_dict.get(full_symbol,None)
            if price != None:
                high = row['high']
                high_diff = round(price - high,2)
                if abs(high_diff)/price < buffer:
                    output['bullish'].append({'symbol':symbol,'price':price,'high':high,'diff':high_diff , 'per':round(high_diff/price,4)})
                
                low = row['low']
                low_diff = round(low - price,2)
                if abs(low_diff)/price < buffer:
                    output['bearish'].append({'symbol':symbol,'price':price,'high':low,'diff':low_diff, 'per':round(low_diff/price,4)})
            else:
                print(full_symbol)
    finally:
        pass
    def get_diff(ele):
        return ele['per']
    output['bullish'].sort(key = get_diff)
    output['bearish'].sort(key = get_diff)
    return output