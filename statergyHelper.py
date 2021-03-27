from requests.api import get
import db
import store
import pandas as pd

def get_latest_signal():
    conn = db.connect()
    res = db.query(conn=conn,query=f''' SELECT DISTINCT stock_symbol, "timestamp",type
	FROM public.stock_statergy
    WHERE is_active = TRUE ''')
    return res

def add_statergy_signal(df):
    """
    Using cursor.mogrify() to build the bulk insert query
    then cursor.execute() to execute the query
   """
    # Check if it is already there
    already_present = get_latest_signal()
    print('already present')
    print(already_present)
    join_df = pd.merge(already_present,df,on=['stock_symbol','type'],how='right',indicator=True)
    df_to_add = join_df[ join_df['_merge'] == 'right_only']
    df_to_add = df_to_add[['stock_symbol','type','timestamp_y','statergy_id']].rename(columns={'timestamp_y':'timestamp'})
    if df_to_add.empty == False :
        res = store.writeToDB(df_to_add,table = 'stock_statergy')
    df_to_delete = join_df[ join_df['_merge'] == 'left_only']
    # df_to_delete = df_to_delete[['id']]
    if df_to_delete.empty == False :
       pass 
       # res = store.writeToDB(df_to_delete,table = 'stock_statergy')
    return df_to_delete.empty == False or df_to_add.empty == False