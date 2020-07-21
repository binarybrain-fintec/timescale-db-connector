import paho.mqtt.client as paho
from datetime import datetime, time
from time import sleep
import pandas
import logging
import threading
import sys

# Type Hint
from utils.environment import Mqtt2TimescaleEnvironment
from mqtt2timescale.postgres_connector import TimescaleConnector


def init_table(data: str, db_cols: list, client: paho.Client, args: Mqtt2TimescaleEnvironment):
    """
    inits table by inspecting datastructure of received header and data
    """
    is_dict = False
    if "messtellen" in data:
        client.db_con.energy_box = True
        if db_cols:
            if len(db_cols) != 3 + len(data['werte']):
                raise IndexError("cols specified not matching with data")
            cols = db_cols
        else:
            cols = ['id']
            cols.extend(data['messtellen'])
            cols.extend(['unix_timestamp', 'timestamp'])
        client.db_con.cols = cols
        df = create_energy_box_df(data, cols)
    else:
        if db_cols:
            df = pandas.DataFrame([list(data.values())], columns=db_cols)
        else:  # use keys if available, else generic names
            if type(data) == type(dict):
                is_dict = True
                df = pandas.DataFrame([list(data.values())], columns=list(data.keys()))
            else:
                is_dict = False
                df = pandas.DataFrame([list(data.values())])
    if args.timescaledb_replace_existing_table:
        if_exists_str = "replace"
    else:
        if_exists_str = "append"
    try:
        client.db_con.create_table(dframe=df, table_name=args.timescaledb_table_name, compress_after=args.timescaledb_compress_after,
                                   index_column_name=args.timescaledb_index_column, chunking_interval=args.timescaledb_chunking_interval,
                                   if_exists=if_exists_str)
    except Exception as e:
        logging.error(e)
        logging.error("TABLE CREATION FAILED, SHUTTING DOWN APPLICATION")
        client.kill_switch[0] = True
        sys.exit(1)

    if args.timescaledb_drop_chunk_after:
        # Schedule data retention to start after 60 seconds
        rmanager_args = (args.timescaledb_drop_chunk_after, args.timescaledb_table_name, client.db_con)
        client.db_con.data_retention_manager_thread = threading.Timer(60, data_retention_manager, rmanager_args)
        client.db_con.data_retention_manager_thread.start()

    client.db_con.table_created = True

    return is_dict


def create_energy_box_df(data, cols):
    dat = [data['id']]
    dat.extend(data['werte'])
    dat.extend([data['zeit'], convert_unixmilli_to_datetime(data['zeit'])])
    return pandas.DataFrame([dat], columns=cols)


def convert_unixmilli_to_datetime(unixmilli_time):
    t = int(float(unixmilli_time) / 1000)
    t_string = datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
    t_string = t_string + ".{0:03d}".format(int(unixmilli_time - t * 1000))
    return datetime.strptime(t_string, '%Y-%m-%d %H:%M:%S.%f')


def data_retention_manager(drop_chunk_after: str, table_name: str, db_con: TimescaleConnector):
    """
    calls drop chunks once a minute
    """
    while not sleep(60):
        try:
            if not drop_chunk_after == "never":
                cur = db_con.conn.cursor()
                cur.execute(f"SELECT drop_chunks(interval '{drop_chunk_after}', '{table_name}');")
                db_con.conn.commit()
        except Exception as e:
            logging.error(e)
            logging.error("ERROR DURING DATA RETENTION MANAGEMENT")
            sys.exit(1)