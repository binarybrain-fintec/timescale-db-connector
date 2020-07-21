import psycopg2
from sqlalchemy import create_engine
from pandas import DataFrame
from datetime import datetime, timedelta
from ttictoc import TicToc
from time import sleep

import logging
import os
import psutil
import io


class PostgresConnector:

    def __init__(self, db_address="localhost", user="postgres", password="password", db_name="postgres",
                 table_name="datenpunkt"):
        self.db_address = db_address
        self.user = user
        self.pw = password
        self.db_name = db_name
        self.table_name = table_name

        self.commands = {
            "get_columns":
                """
                SELECT *
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = N'{}'
                """.format(self.table_name),
            "get_data":
                """
                SELECT * FROM public.{} WHERE {} BETWEEN {} AND {}
                ORDER BY {} ASC, {} ASC, {} ASC
                """,
            "get_time_slice":
                """
                SELECT * FROM public.{} WHERE {} BETWEEN \'{}\' AND \'{}\' ORDER BY {} ASC
                """
        }

        self.conn = self.connect()

        self.cache_df = {}

    def __del__(self):
        try:
            if self.conn:
                self.conn.close()
                print('Database connection closed.')
        except AttributeError:
            pass

    def connect(self):
        """ Connect to the PostgreSQL database server """
        conn = None
        try:
            # connect to the PostgreSQL server
            print('Connecting to the PostgreSQL database...')
            address = self.db_address.split(":")[0]
            if len(self.db_address.split(":")) > 1:
                port = int(self.db_address.split(":")[1])
            else:
                port = 5432

            while True:
                try:
                    conn = psycopg2.connect(host=address, port=port, database=self.db_name, user=self.user, password=self.pw)
                    self.engine = create_engine(
                        f'postgresql+psycopg2://{self.user}:{self.pw}@{address}:{port}/{self.db_name}')
                    # create a cursor
                    cur = conn.cursor()
                    break
                except Exception as e:
                    print(e)
                    sleep(1)

            # execute a statement
            print('PostgreSQL database version:')
            cur.execute('SELECT version()')

            # display the PostgreSQL database server version
            db_version = cur.fetchone()
            print(db_version)

            # get columns
            cur = conn.cursor()
            cur.execute(self.commands["get_columns"])
            df = DataFrame(cur.fetchall())
            self.cols = list(df.columns)

            # close the communication with the PostgreSQL
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            if conn:
                conn.close()
            raise error
        return conn

    def create_table(self, dframe: DataFrame, table_name: str = None, index_column_name: str = None, if_exists="fail"):
        """
        creates a new table
        """
        t = TicToc()
        t.tic()
        if not table_name:
            table_name = self.table_name
        if not index_column_name:
            index_column_name = dframe.columns[0]
        dframe.head(0).to_sql(table_name, self.engine, if_exists=if_exists, index=False, index_label=index_column_name)
        t.toc()
        logging.info(f"Created new table {table_name} in {t.elapsed} seconds")

    def append_table(self, dframe: DataFrame, table_name: str = None):
        """
        appends to existing sql table by creating a csv and then commiting it
        """
        t = TicToc()
        t.tic()
        logging.info(f"Writing {len(dframe)} rows to {table_name}...")
        if not table_name:
            table_name = self.table_name
        c = self.engine.raw_connection()
        cur = c.cursor()
        output = io.StringIO()
        dframe.to_csv(output, sep='\t', header=False, index=False)
        output.seek(0)
        cur.copy_from(output, table_name, null="")  # null values become ''
        c.commit()
        t.toc()
        logging.info(f"Written {len(dframe)} rows to {table_name} in {t.elapsed} seconds")

    def convert_unixmilli_to_datetime(self, unixmilli_time):
        t = int(float(unixmilli_time) / 1000)
        #t_string = datetime.utcfromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
        t_string = datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
        t_string = t_string + ".{}".format(int(unixmilli_time - t * 1000))
        return datetime.strptime(t_string, '%Y-%m-%d %H:%M:%S.%03f')

    def convert_to_datetime(self, time):
        _datetime = []
        for t in time:
            _datetime.append(self.convert_unixmilli_to_datetime(t))
        return _datetime

    def convert_datetime_to_unixmilli(self, _datetime):
        return int(_datetime.timestamp() * 1000) # + 7200000)  # - 1559602800000)

    def retrieve_data_slice(self, start_date_str='2019-07-23 08:00:00', stop_date_str='2019-07-23 10:00:00'):
        d1_datetime = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
        d2_datetime = datetime.strptime(stop_date_str, '%Y-%m-%d %H:%M:%S')
        key = start_date_str + ";" + stop_date_str
        d2 = self.convert_datetime_to_unixmilli(d2_datetime)
        d1 = self.convert_datetime_to_unixmilli(d1_datetime)

        if key in self.cache_df:
            return self.cache_df[key]
        else:
            if self.conn:
                try:
                    com = self.commands["get_data"].format(self.table_name,
                                                  self.cols[0],
                                                  d1, d2,
                                                  self.cols[0], self.cols[1], self.cols[2], self.cols[3])
                    cur = self.conn.cursor()
                    cur.execute(com)
                    df = DataFrame(cur.fetchall(), columns=self.cols)
                    df.insert(0, "datetime", self.convert_to_datetime(df[self.cols[0]]))
                    print("retrieved {} rows".format(len(df)))
                    self.cache_df[key] = df
                    return df
                except (Exception, psycopg2.DatabaseError) as error:
                    print(error)


class TimescaleConnector(PostgresConnector):
    """
    For TimescaleDB optimized connector.
    Can be used as iterator.

    Example:
        # Init Connector
        conn = TimescaleConnector(db_address="localhost", user="postgres", password="902243", db_name="power_hyper",
                 table_name="energy_data")

        # Get data slice
        data = conn.retrieve_data_slice(start_date='2019-07-23 08:00:00', end_date='2019-07-23 10:00:00')

        # Set step size for iteration in days. Step size is 1 day per default.
        conn.set_iter_step_size(days=1)
        # Iterate over DB for 3 steps
        i = 1
        for df in conn:
            print(df.iloc[0])
            i = i + 1
            if i > 3:
                break
    """
    def __init__(self, db_address="localhost", user="postgres", password="password", db_name="postgres",
                 table_name="dat"):
        super(TimescaleConnector, self).__init__(db_address, user, password, db_name, table_name)
        self.process = psutil.Process(os.getpid())
        self.iter_timedelta: timedelta = timedelta(days=1)  # Change this to get larger data slices
        self.start_date: datetime = datetime.strptime("2019-07-23 08:00:00", '%Y-%m-%d %H:%M:%S')
        self.iter_date: datetime = self.start_date
        logging.info("Getting first timestamp")
        self.min_date = self.get_first_timestamp()
        logging.info("Getting last timestamp")
        self.max_date = self.get_last_timestamp()
        logging.info(f"Access to timescaleDB with name {self.db_name} "
                     f"timestamps between {self.min_date} and {self.max_date}")

    def __setattr__(self, key, value):
        """
        Typesafe Setter
        """
        try:
            attr = self.__getattribute__(key)
            if type(attr) is not type(value):
                raise TypeError(f"{value} is not of type {type(attr)}")
            else:
                self.__dict__[key] = value
        except AttributeError:
            self.__dict__[key] = value

    def __iter__(self):
        self.iter_date = self.min_date
        return self

    def __next__(self) -> DataFrame:
        if self.iter_date < self.max_date:
            data_slice = self.retrieve_data_slice(str(self.iter_date), str(self.iter_date + self.iter_timedelta))
            self.iter_date = self.iter_date + self.iter_timedelta
            return data_slice
        else:
            raise StopIteration

    def create_table(self, dframe: DataFrame, table_name: str = None, compress_after: str = None, compression_segment_by: str = None, index_column_name: str = None, chunking_interval: str = '7 days', if_exists="fail"):
        """
        creates a new hyper table or appends to existing
        """
        t = TicToc()
        t.tic()

        if not table_name:
            table_name = self.table_name

        cur = self.conn.cursor()
        cur.execute(f"SELECT EXISTS(SELECT * FROM _timescaledb_catalog.hypertable WHERE table_name='{table_name}')", (f'{table_name}',))
        table_already_hypertable = cur.fetchone()[0]

        if not index_column_name:
            index_column_name = dframe.columns[0]

        # Load explicitly extentions
        ex_str = "SELECT * FROM pg_extension;"
        ex_str += "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"

        # Throws, if columns are not consistent to existing table, otherwise creates new table
        dframe.head(0).to_sql(table_name, self.engine, if_exists=if_exists, index=False, index_label=index_column_name)
        if not table_already_hypertable or if_exists == "replace":
            ex_str += f"SELECT create_hypertable('{table_name}', '{index_column_name}', chunk_time_interval => interval '{chunking_interval}', migrate_data => true);"

            if compress_after:
                if not compression_segment_by:
                    compression_segment_by = index_column_name

                ex_str += f"""
                ALTER TABLE {table_name} SET (timescaledb.compress, timescaledb.compress_segmentby = '{compression_segment_by}');
                SELECT add_compress_chunks_policy('{table_name}', INTERVAL '{compress_after}');
                """
                logging.info(f"Defined for table {table_name} data compression after {compress_after}")

        cur.execute(ex_str)
        self.conn.commit()
        t.toc()
        logging.info(f"Created new table {table_name} in {t.elapsed} seconds")

    def set_iter_step_size(self, days: float) -> None:
        self.iter_timedelta = timedelta(days=days)

    def retrieve_data_slice(self, start_date='2019-07-23 08:00:00', end_date='2019-07-23 10:00:00', use_caching=False, table_name=None) -> DataFrame:
        if use_caching:
            key = start_date + ";" + end_date
            if key in self.cache_df:
                return self.cache_df[key]

        t = TicToc()  ## TicToc("name")
        t.tic()

        if self.conn:
            try:
                query_str = self.commands["get_time_slice"].format(self.table_name, self.cols[0],
                                                                   start_date, end_date, self.cols[0])
                logging.info("Retrieving time slice between {} and {}".format(start_date, end_date))
                cur = self.conn.cursor()
                cur.execute(query_str)
                df = DataFrame(cur.fetchall(), columns=self.cols)
                t.toc()
                memory_usage = self.process.memory_info().rss
                logging.info(f"Retrieved { len(df) } rows in {t.elapsed:.3} seconds. Using {memory_usage/(1024*1000)} MB memory.")
                if use_caching:
                    self.cache_df[key] = df
                return df
            except (Exception, psycopg2.DatabaseError) as error:
                print(error)

    def get_last_row(self) -> DataFrame:
        if self.conn:
            try:
                query_str = f"""
                    SELECT * FROM { self.table_name } t1
                    WHERE { self.cols[0] } = (SELECT MAX({ self.cols[0]}) FROM { self.table_name });
                """
                cur = self.conn.cursor()
                cur.execute(query_str)
                return DataFrame(cur.fetchall(), columns=self.cols)
            except (Exception, psycopg2.DatabaseError) as error:
                print(error)

    def get_last_timestamp(self) -> datetime:
        if self.conn:
            try:
                query_str = f"SELECT MAX({ self.cols[0]} ) FROM { self.table_name };"
                cur = self.conn.cursor()
                cur.execute(query_str)
                return cur.fetchall()[0][0]
            except (Exception, psycopg2.DatabaseError) as error:
                print(error)

    def get_first_timestamp(self) -> datetime:
        """ignores all 1970s timestamps on purpose"""
        if self.conn:
            try:
                query_str = f"SELECT MIN({ self.cols[0] } ) FROM { self.table_name } WHERE { self.cols[0] } > '2010-01-01';"
                cur = self.conn.cursor()
                cur.execute(query_str)
                return cur.fetchall()[0][0]
            except (Exception, psycopg2.DatabaseError) as error:
                print(error)


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] \t %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

    conn = TimescaleConnector(db_address="localhost", user="postgres", password="902243", db_name="power_hyper",
                 table_name="energy_data")

    df = conn.retrieve_data_slice()
    # Create new table from df and replace existing ones
    conn.create_table(df, table_name="test_table", if_exists="replace")
    conn.set_iter_step_size(days=30)
    i = 1
    # Iterate over DB
    for df in conn:
        print(df.iloc[0])
        # Write slice to the new table
        conn.append_table(df, "test_table")
        i = i + 1
        if i > 2:
            break

