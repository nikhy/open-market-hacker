import pandas as pd

import nsepy


import db
from config import config

import logging

# Import date and timdelta class
# from datetime module
from datetime import date
from datetime import timedelta
from datetime import datetime


def getHistoryData(kite, ins_token, date1, date2, interval):
    result = kite.historical_data(
        instrument_token=ins_token,
        from_date=date1,
        to_date=date2,
        interval=interval,
        #continuous=True,
    )
    return result


def getMaxDate():
    conn = db.connect()
    df = db.query(
        conn, "SELECT max(timestamp) AS max_timestamp FROM tdb_stock_price_intraday"
    )
    return df


def getStockData():
    conn = db.connect()
    nifty50Map = db.query(conn, "SELECT id,zerodha_token, symbol, name FROM stock")
    nifty50Map = nifty50Map.set_index("zerodha_token")
    nifty50Map = nifty50Map.to_dict()
    nifty50Map = nifty50Map["id"]
    return nifty50Map


def getFullPriceData(kite, dayRange, interval):
    fullDf = pd.DataFrame()
    stockData = getStockData()
    today = datetime.now()
    start = today - timedelta(days=dayRange)
    end = today
    max_date_df = getMaxDate()
    max_timestamp = max_date_df["max_timestamp"][0]
    if max_timestamp:
        start = pd.to_datetime(max_date_df["max_timestamp"][0])
        print(f""" start from db {start}""")
        start += timedelta(0, 1)
    print(f"""start{start} ; end {end}""")
    date1 = start
    date2 = start + timedelta(days=60)
    if date2 > end:
        date2 = end
    while end >= date1:
        fullDf = pd.DataFrame()
        strDate1 = date1.strftime("%Y-%m-%d %H:%M:%S")
        strDate2 = date2.strftime("%Y-%m-%d") + " 23:59:59"
        print(strDate1, strDate2)
        for instr in stockData:
            rawData = getHistoryData(kite, instr, strDate1, strDate2, interval)
            df = pd.DataFrame(rawData)
            df["stock_id"] = pd.Series(
                [stockData[instr] for x in range(len(df.index))], index=df.index
            )
            if fullDf.empty:
                fullDf = df
            else:
                fullDf = fullDf.append(df)
        if fullDf.empty != True:
            writeToDB(fullDf, table="tdb_stock_price_intraday")
        else:
            print(f""" empty df """)
        date1 = date1 + timedelta(days=60)
        date2 = date2 + timedelta(days=60)
    return fullDf


def writeToDB(df, table="stock_price"):
    conn = db.connect()
    df = df.rename(columns={"date": "timestamp"})
    db.execute_mogrify(conn, df, table)
    db.putback_conn(conn)


def getNSEPyHistoryData(stock, start, end):
    rawData = nsepy.get_history(symbol=stock, start=start, end=end)
    rawData = pd.DataFrame(rawData)
    rawData.reset_index(inplace=True)
    rawData = rawData.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
            "Date": "date",
        }
    )
    return rawData


def getInstruments(kite):
    result = kite.instruments(exchange="nse")
    return result


def getNSEPyFullPriceData(dayRange):
    stockData = getStockData()
    today = datetime.now()
    date2 = today
    max_date_df = getMaxDate()
    max_timestamp = max_date_df["max_timestamp"][0]
    if max_timestamp:
        date1 = max_timestamp
    else:
        date1 = today - timedelta(days=dayRange)
    fullDf = pd.DataFrame()
    for instr in stockData:
        df = getNSEPyHistoryData(instr, date1, date2)
        df["stock_id"] = pd.Series(
            [stockData[instr] for x in range(len(df.index))], index=df.index
        )
        if fullDf.empty:
            fullDf = df
        else:
            fullDf = fullDf.append(df)
    fullDf = fullDf[["date", "open", "high", "low", "close", "volume", "stock_id"]]
    return fullDf