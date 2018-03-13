import sqlite3
import pandas as pd

def connect():
    connection = sqlite3.connect("NBA_data.db")
    connection.commit()
    connection.close()

connect() #Must call the connect function incase the user hasn't got the database file

#Define functions for interacting with database
def add_result(result_df):
    connection = sqlite3.connect("NBA_data.db")
    result_df.to_sql("results", connection, if_exists="append", index=False)
    connection.commit()
    connection.close()

def add_boxscore(boxscore_df):
    connection = sqlite3.connect("NBA_data.db")
    boxscore_df.to_sql("boxscores", connection, if_exists="append", index=False)
    connection.commit()
    connection.close()

def retrieve_all_results():
    con = sqlite3.connect("NBA_data.db")
    try:
        sql = "SELECT * from results"
        data = pd.read_sql(sql, con) #parse_dates={'gamedate':"%d/%m/%Y"})
    except (sqlite3.OperationalError, pd.io.sql.DatabaseError):
        data = pd.DataFrame()
    return data

def retrieve_all_boxscores():
    con = sqlite3.connect("NBA_data.db")
    try:
        sql = "SELECT * from boxscores"
        data = pd.read_sql(sql, con)
    except sqlite3.OperationalError:
        data = pd.DataFrame()
    return data

def delete_by_date(date):
    con = sqlite3.connect("NBA_data.db")
    try:
        sql = "SELECT * from results"
        data = pd.read_sql(sql, con)
        gameids = data[data['gamedate'] == date]['gameid']
        cursor = con.cursor()
        for gameid in gameids.values:
            cursor.execute("DELETE * FROM boxscores WHERE gameid = ?", (gameid))

        cursor.execute("DELETE * FROM results WHERE gamedate = ?", (date))
        con.commit()
    except sqlite3.OperationalError:
        print('No games to delete with that date.')
#Finish defining functions
