import db
def getPriceData(dayInterval):
    conn = db.connect()
    df = db.query(conn,
    f'''SELECT s.symbol,s.name,sp.* from stock_price sp 
        INNER JOIN stock s ON s.id = sp.stock_id
        WHERE timestamp > now() -  INTERVAL '{dayInterval} days'
        ORDER BY s.name,timestamp
        ''')
    df = df.rename(columns={'timestamp':'datetime'})
    return df

def getMinutePriceData(start,end,stockSymbol = ''):
    nameClause = ''
    if stockSymbol != '':
        nameClause = f''' and s.symbol = '{stockSymbol}' '''
    conn = db.connect()
    sqlQuery = f'''SELECT s.symbol,s.name,sp.* from tdb_stock_price_intraday sp 
        INNER JOIN stock s ON s.id = sp.stock_id {nameClause}
        WHERE timestamp >= '{start}' and timestamp <= '{end}' 
        ORDER BY s.name,timestamp
        '''
    df = db.query(conn,sqlQuery)
    df = df.rename(columns={'timestamp':'datetime'})
    return df

def getNifty50MinutePriceData(start,end):
    conn = db.connect()
    sqlQuery = f'''SELECT s.symbol,s.name,sp.* from tdb_stock_price_intraday sp 
        INNER JOIN stock s ON s.id = sp.stock_id 
        INNER JOIN basket_stock bs ON bs.stock_id = s.id
        INNER JOIN basket b ON b.name = 'NIFTY50'   and b.id = bs.basket_id     
        WHERE timestamp >= '{start}' and timestamp <= '{end}' 
        ORDER BY s.name,timestamp
        '''
    df = db.query(conn,sqlQuery)
    df = df.rename(columns={'timestamp':'datetime'})
    return df

def getStockData():
    conn = db.connect()
    nifty50Map = db.query(conn,'SELECT id,zerodha_token, symbol, name FROM stock')
    return nifty50Map



    