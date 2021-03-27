#!/usr/bin/python
import psycopg2
from psycopg2.extras import execute_values
from psycopg2 import pool
from config import config
import pandas.io.sql as sqlio
import pandas as pd
postgreSQL_pool = ""
def putback_conn(conn):
    global postgreSQL_pool
    if(postgreSQL_pool != ""):
        postgreSQL_pool.putconn(conn)
def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        global postgreSQL_pool
        params = config()
        if(postgreSQL_pool == ""):
            postgreSQL_pool = psycopg2.pool.SimpleConnectionPool(1, 20,**params)
        
            print("Connection pool created successfully")
        conn = postgreSQL_pool.getconn()
	# close the communication with the PostgreSQL
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        if conn is not None:
            conn.close()
            print('Database connection closed.')
    return conn

def execute_mogrify(conn, df, table):
    """
    Using cursor.mogrify() to build the bulk insert query
    then cursor.execute() to execute the query
    """
    cursor = conn.cursor()
    query  = f'''INSERT INTO {table}({','.join(list(df.columns))}) VALUES %s ''' 
    try:
        print(query)
        execute_values(cursor,query, [tuple(x) for x in df.to_numpy()])
        conn.commit()
        print("execute_mogrify() done")    
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        conn.rollback()
    finally:
        cursor.close()
def query(conn ,query):
    """
    Using cursor.mogrify() to build the bulk insert query
    then cursor.execute() to execute the query
    """
    try:
        df = sqlio.read_sql_query(query, conn)
    except (Exception, psycopg2.DatabaseError) as error:
        print(" DB Error: %s" % error)
        if conn is not None:
            conn.rollback()
        return 1
    finally:
        if conn is not None:
            putback_conn(conn)

    return df



def delete_part(table,col,val):
    """ delete part by condition """
    conn = None
    rows_deleted = 0
    try:
        # connect to the PostgreSQL database
        conn = connect()
        # create a new cursor
        cur = conn.cursor()
        # execute the UPDATE  statement
        cur.execute("DELETE FROM %s WHERE %s = %s", (table,col,val))
        # get the number of updated rows
        rows_deleted = cur.rowcount
        # Commit the changes to the database
        conn.commit()
        # Close communication with the PostgreSQL database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            putback_conn(conn)

    return rows_deleted