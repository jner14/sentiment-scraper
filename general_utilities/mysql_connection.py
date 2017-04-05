import sqlalchemy
import pandas as pd
import numpy as np


class MySqlConnector(object):

    def __init__(self, url):
        self.url     = url
        self._engine = None
        self._conn   = None
        self.connect(url)

    def connect(self, url: str):
        self.url = url
        self._engine = sqlalchemy.create_engine(url)
        self._conn = self._engine.connect()

    def write_table(self, table_name: str, dataframe: pd.DataFrame, mode: str='append'):
        dataframe.to_sql(name=table_name, con=self._conn, if_exists=mode)

    def read_table(self, table_name: str) -> pd.DataFrame:
        return pd.read_sql_table(table_name=table_name, con=self._conn, index_col='index')

    def drop_table(self, table_name: str):
        metadata = sqlalchemy.MetaData()
        metadata.reflect(bind=self._engine)
        if table_name in metadata.tables:
            table = metadata.tables[table_name]
            table.drop(self._engine)
            print("%s dropped." % table_name)
        else:
            print("%s not dropped because it doesn't exist." % table_name)
