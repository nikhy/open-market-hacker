import urllib
import logging


from datetime import datetime
from kiteconnect import KiteConnect

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

import pandas as pd
import store
from config import config
import json
from scanners.setup_1 import Setup1Scanner
from scanners.donchain_1 import scan as donchain_scan
import statergyHelper

from tv_statergies.day_zone_refresh import refresh_day_zone
from tv_statergies.day_zone import day_zone_scanner
from tv_statergies.day_zone_zerodha import day_zone_scanner_zerodha

from pattern_matrix import pattern_matrix
import telegram as telegram
templates = Jinja2Templates(directory="templates")


access_token = None

app = FastAPI()

zerodhaParams = config(filename ='zerodha.ini',section='zerodha')
kite = KiteConnect(zerodhaParams['api_key'])

@app.get("/patternMatrix/{dayRange}")
def read_root(dayRange, request: Request):
    global candlestick_patterns
    stocks = pattern_matrix(dayRange)
    return stocks

@app.get("/zerodha")
def zerodha(request_token=None, redirect_url=''):
    global kite
    global access_token
    if request_token != None:
        logging.info('requestToken = %s', request_token)
        session = kite.generate_session(request_token, api_secret=zerodhaParams['api_secret'])
        access_token = session['access_token']
        logging.info('access_token = %s', access_token)
        kite.set_access_token(access_token)
        logging.info('Login successful. access_token = %s', access_token)
        # redirect to home page with query param loggedIn=true
        home_url = redirect_url
        logging.info('Redirecting to home page %s', home_url)
        return RedirectResponse(home_url)
    else:
        loginUrl = kite.login_url()
        logging.info('Redirecting to zerodha login url = %s', loginUrl)
        return RedirectResponse(loginUrl)


@app.get("/stocks")
def get_stocks():
    res = store.getStockData()
    return res


@app.get("/loadData/{source}/{dayRange}")
def load_data(source, dayRange, request:Request):
    if source == "zerodha":
        if access_token == None:
            login_url = kite.login_url()
            encodedParams = urllib.parse.quote(f"""redirect_url={request.url}""")
            url = f"""{login_url}&redirect_params={encodedParams}"""
            return RedirectResponse(url=url)
        else:
            df = store.getFullPriceData(kite, int(dayRange), "minute")
    elif source == "nsepy":
        dayRange = int(dayRange)
        df = store.getNSEPyFullPriceData(dayRange)
        store.writeToDB(df)
    return {'sucess':True}


@app.get("/instruments")
def get_instruments():
    global kite
    res = store.getInstruments(kite)
    return res


@app.get("/scanners/{scanner}")
def get_scanner(scanner):
    global kite
    df = store.getFullPriceData(kite, int(1), "minute")
    res = Setup1Scanner()
    return res


@app.get("/tv/refresh")
def f():
    res = refresh_day_zone()
    return res


@app.get("/tv/scan", response_class=HTMLResponse)
def selenium_scan(request: Request):
    res = day_zone_scanner()
    return templates.TemplateResponse(
        "day_zone.html",
        {
            "request": request,
            "stocks1": res["bullish"],
            "stocks2": res["bearish"],
            "time_taken":res["time_taken"],
            "time":datetime.now()
        },
    )


@app.get("/{s}")
def f1(s,request:Request):
    return {"url": request.url }



@app.get("/tv/zerodha/scan", response_class=HTMLResponse)
def scan(request: Request):
    global access_token
    if access_token == None:
        login_url = kite.login_url()
        encodedParams = urllib.parse.quote(f"""redirect_url={request.url}""")
        url = f"""{login_url}&redirect_params={encodedParams}"""
        return RedirectResponse(url=url)
    else:
        res = day_zone_scanner_zerodha(kite = kite)
        return templates.TemplateResponse(
            "day_zone.html",
            {
                "request": request,
                "stocks1": res["bullish"],
                "stocks2": res["bearish"],
                # "time_taken":res["time_taken"],
                "time":datetime.now()
            },
        )


@app.get("/statergies/dc")
def dc_scan(request:Request):
    if access_token == None:
        login_url = kite.login_url()
        encodedParams = urllib.parse.quote(f"""redirect_url={request.url}""")
        url = f"""{login_url}&redirect_params={encodedParams}"""
        return RedirectResponse(url=url)
    else:
        res = donchain_scan(kite)
        print('scanned res')
        print(res)
        # if len(res) != 0: 
        #     statergyHelper.add_statergy_signal(pd.DataFrame(res))
        # res = statergyHelper.get_latest_signal()
        # print(res)
        msg = res
        if (len(res) != 0 ): 
            print('sending msg')
            res = pd.DataFrame(res)
            res.rename(columns={"stock_symbol":"symhol"})
            msg = res.to_json()
            print(f'msg:{msg}')
            tr = telegram.telegram_bot_sendtext(msg)
            print(tr)
        return {
            'sucess':True,
            'data':msg
        }