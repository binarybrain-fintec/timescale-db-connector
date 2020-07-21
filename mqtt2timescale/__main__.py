#!/usr/bin/env python3
from multiprocessing import shared_memory
import logging
import signal
import json

from flask import Flask, request
from multiprocessing import Process

from mqtt2timescale.postgres_connector import TimescaleConnector
from mqtt2timescale.mqtt_app import setup_mqtt
from utils.environment import Mqtt2TimescaleEnvironment

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] \t %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')

kill_switch = shared_memory.ShareableList([False]) # Alloc Memory for kill_switch


def health_event_loop(args):
    app = Flask(__name__)

    @app.route('/api/health', methods=['GET'])  # allow both GET and POST requests
    def health():
        logging.info(request.get_data())
        return json.dumps({'UP': "OK"}), 200, {'ContentType': 'application/json'}

    port = args.host.split(":")[1]
    app.run(host='0.0.0.0', port=port)


def sigterm_handler(_signo, _stack_frame):
    """
    Activates the kill_switch, if SIGNAL was raised
    """
    kill_switch[0] = True


def main(env: Mqtt2TimescaleEnvironment):
    # Setting signal handlers for Interrupt and Terminate
    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    # Uncomment for debugging. Breakpoints do not work inside processes!
    Process(target=health_event_loop, args=(env,))

    # Main Application
    timescale_con = TimescaleConnector(db_address=env.timescaledb_host, user=env.timescaledb_username,
                                       password=env.timescaledb_password, db_name=env.timescaledb_name)
    timescale_con.table_created = False

    client = setup_mqtt(env, timescale_con, kill_switch)

    # Heartbeat loop for rabbitmq
    while not kill_switch[0]:
        client.loop_forever(timeout=60, retry_first_connection=False, max_packets=99)
    client.disconnect()
