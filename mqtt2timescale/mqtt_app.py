import paho.mqtt.client as paho
import pandas
import json
import logging
from time import sleep

from mqtt2timescale.data_utils import init_table, create_energy_box_df

# Type Hint
from utils.environment import Mqtt2TimescaleEnvironment
from mqtt2timescale.postgres_connector import TimescaleConnector
from multiprocessing import shared_memory


def setup_mqtt(args: Mqtt2TimescaleEnvironment, timescale_con: TimescaleConnector, kill_switch: shared_memory) -> paho.Client:
    """
    Creates mqtt client
    """
    # Init mqtt client
    client = paho.Client(args.service_name)  # create client object
    client.username_pw_set(args.mqtt_client_username, args.mqtt_client_password)

    db_cols = None
    if args.timescaledb_header_string:
        db_cols = args.timescaledb_header_string.split(";")

    client.db_con = timescale_con
    client.db_con.table_created = False
    client.db_con.energy_box = False
    client.db_cols = db_cols
    client.env_args = args
    client.on_message = on_message  # assign function to callback
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.kill_switch = kill_switch

    # Trying to connect
    host, port = args.mqtt_client_host.split(":")
    client.mqtt_client_topic = args.mqtt_client_topic
    while True:
        try:
            client.connect(host, int(port), keepalive=60)  # establish connection
            break
        except Exception as e:
            logging.error(e)

    return client


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(client.mqtt_client_topic, qos=2)
        client.will_set(client.mqtt_client_topic, payload=None, qos=2, retain=True)
        logging.info(f"Connected to topic: {client.mqtt_client_topic}")
    else:
        logging.warning(f"Connection failed, error code {rc}")


def on_disconnect(client, userdata, flags, rc):
    print(rc)


def on_message(client, _u, msg):
    """
    defines callback for message handling, inits db table from first data row received
    """
    data = json.loads(msg.payload.decode("utf-8"))[0]
    if not client.db_con.table_created:
        client.data_is_dict = init_table(data, client.db_cols, client, client.env_args)
    if "messtellen" in data:
        df = create_energy_box_df(data, client.db_con.cols)
    else:
        if client.data_is_dict:
            df = pandas.DataFrame(list(data.values()), columns=list(data.keys()))
        else:
            df = pandas.DataFrame(list(data.values()))
    client.db_con.append_table(df, client.env_args.timescaledb_table_name)
    logging.info(f"wrote {data} to table {client.env_args.timescaledb_table_name}")
