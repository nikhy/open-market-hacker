from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options

from datetime import datetime 
import time 
import pandas as pd
from config import config


tv_config = config(filename='tv.ini',section='tv')

def refresh_day_zone():
    options = Options()
    options.headless = True

    output = {}
    #driver = webdriver.Firefox(options = options)
    driver = webdriver.Firefox()

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
            EC.presence_of_element_located((By.XPATH, '''//*[contains(text(), 'nikhy')]'''))
        )
        driver.get('''https://in.tradingview.com/chart?symbol=NSE%3AADANIPORTS''')
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '''/html/body/div[2]/div[5]/div/div[2]/div/div/div/div/div[1]/span'''))
        )
        #elem = driver.find_element_by_xpath("/html/body/div[2]/div[5]/div/div[2]/div/div/div/div/div[1]/span")
        #elem.click()

        symbols = ['ADANIPORTS', 'ASIANPAINT', 'AXISBANK', 'BAJAJFINSV', 'BAJAJ_AUTO', 'BAJFINANCE', 'BHARTIARTL', 'BPCL', 'BRITANNIA', 'CIPLA', 
        'COALINDIA', 'DRREDDY', 'EICHERMOT','GAIL', 'HCLTECH', 'HDFC', 'HDFCBANK', 'HEROMOTOCO', 'HINDALCO',
        'HINDUNILVR', 'ICICIBANK', 'INDUSINDBK', 'INFY', 'IOC', 'JSWSTEEL', 'KOTAKBANK', 'LT', 'MARUTI','MINDTREE','M_M',
        'NESTLEIND', 'NTPC', 'ONGC', 'POWERGRID', 'RELIANCE', 'SBILIFE', 'SBIN', 'SHREECEM', 'SUNPHARMA', 'TATAMOTORS',
        'TATASTEEL', 'TCS', 'TECHM', 'TITAN', 'ULTRACEMCO', 'UPL', 'VEDL', 'WIPRO', 'ZEEL']
        for symbol in symbols:
            print(symbol)
            elem = driver.find_element_by_xpath(f'''//span[contains(text(), '{symbol}')]''')
            parent = driver.find_element_by_xpath(f'''//div[@data-symbol-short='{symbol}']''')
            time.sleep(1)        
            price_elements = parent.find_element_by_css_selector(f'''span.cell-2dpljH_9.last-31ae42tU''').find_elements_by_tag_name('span')
            price = ''
            c = 0
            for price_ele in price_elements:
                c+=1
                if(c>1):
                    break
                price += price_ele.text
            price = float(price)
            elem.click()   
            element = WebDriverWait(driver, 10).until(
                EC.title_contains(symbol)
            )
            time.sleep(4)
            output[symbol] = {'price':price,'symbol':symbol}
            zone_values_arr = []
            for i in [1,2,3,4] :
                n = f'''data_{i}'''
                data_elem = driver.find_element_by_xpath(f'''/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[1]/div[2]/div[2]/div[2]/div[2]/div/div[{i}]/div''')
                output[symbol][n] = data_elem.text    
                zone_values_arr.append(data_elem.text)
            output[symbol]['high'] = max(zone_values_arr)
            output[symbol]['low'] = min(zone_values_arr)
    finally:
        driver.quit() 
        pass

    df = pd.DataFrame(output).T
    df.to_csv('data/day_zones.csv')
    return df.to_dict()