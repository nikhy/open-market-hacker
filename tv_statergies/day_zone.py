from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options

import time 
import pandas as pd
from config import config
from datetime import datetime

tv_config = config(filename='tv.ini',section='tv')



def day_zone_scanner():
    start_time = datetime.now()
    options = Options()
    options.headless = True

    output = { 'bearish':[] , 'bullish':[] }
    driver = webdriver.Firefox(options = options)
    #driver = webdriver.Firefox()
    buffer = 0.005
    try:

        driver.get("https://in.tradingview.com/")
        elem = driver.find_element_by_xpath("/html/body/div[2]/div[3]/div/div[4]/span[2]/a")
        elem.click()
        driver.implicitly_wait(5)
        elem = driver.find_element_by_css_selector(".tv-signin-dialog__social.tv-signin-dialog__toggle-email.js-show-email")
        elem.click()

        elem = driver.find_element_by_css_selector('''input[name='username']''')
        elem.send_keys(tv_config['user'])

        elem = driver.find_element_by_css_selector('''input[name='password']''')
        elem.send_keys(tv_config['pwd'])

        elem = driver.find_element_by_css_selector('''button[type='submit']''')
        elem.click()
    
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '''//span[contains(text(), 'ADANIPORTS')]'''))
        )
        #elem = driver.find_element_by_xpath("/html/body/div[2]/div[5]/div/div[2]/div/div/div/div/div[1]/span")
        #elem.click()
        df = pd.read_csv('data/day_zones.csv')
        for index, row in df.iterrows(): 
            symbol = (row["symbol"]) 
            elem = driver.find_element_by_xpath(f'''//span[contains(text(), '{symbol}')]''')
            elem.click()           
            parent = driver.find_element_by_xpath(f'''//div[@data-symbol-short='{symbol}']''')
            price_elements = parent.find_element_by_css_selector(f'''span.cell-2dpljH_9.last-31ae42tU''').find_elements_by_tag_name('span')
            price = ''
            c = 1
            for price_ele in price_elements:
                c+=1
                if(c>2):
                    break
                price += price_ele.text
            price = float(price)
            high = row['high']
            high_diff = round(price - high,2)

            if abs(high_diff)/price < buffer:
                output['bullish'].append({'symbol':symbol,'price':price,'high':high,'diff':high_diff , 'per':round(high_diff/price,4)})
            
            low = row['low']
            low_diff = round(low - price,2)
            if abs(low_diff)/price < buffer:
                output['bearish'].append({'symbol':symbol,'price':price,'high':low,'diff':low_diff, 'per':round(low_diff/price,4)})
    finally:
        driver.quit() 
        pass
    def get_diff(ele):
        return ele['per']
    
    output['bullish'].sort(key = get_diff)
    output['bearish'].sort(key = get_diff)
    output['time_taken'] = datetime.now() - start_time
    return output