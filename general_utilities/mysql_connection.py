import sqlalchemy
import pandas as pd
import numpy as np
import sys


class MySqlConnector(object):

    def __init__(self, url, u_name, pwd):
        self.url     = url
        self._engine = None
        self._conn   = None
        self.connect(url, u_name, pwd)

    def connect(self, url: str, user_name: str, pwd: str):
        self.url = url
        self._engine = sqlalchemy.create_engine("mysql+pymysql://{}:{}@{}".format(user_name, pwd, url))
        print("Attempting connection to URL={}, User={}".format(url, user_name))
        try:
            self._conn = self._engine.connect()
            print("Successfully connected.")
        except Exception as e:
            print("Failed to connect! Error={}".format(e))
            sys.exit()

    def write_table(self, table_name: str, dataframe: pd.DataFrame, mode: str='append'):
        dataframe.to_sql(name=table_name, con=self._conn, if_exists=mode, index=False)

    def read_table(self, table_name: str) -> pd.DataFrame:
        return pd.read_sql_table(table_name=table_name, con=self._conn)

    def drop_table(self, table_name: str):
        metadata = sqlalchemy.MetaData()
        metadata.reflect(bind=self._engine)
        if table_name in metadata.tables:
            table = metadata.tables[table_name]
            table.drop(self._engine)
            print("%s dropped." % table_name)
        else:
            print("%s not dropped because it doesn't exist." % table_name)
