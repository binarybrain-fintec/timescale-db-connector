# mqtt2timescale
This service writes dict like rows (keys are columns) into a timescale database. Data needs to be timeseries and to provide a timestamp.

# StartUp
1. It is recommended to use anaconda-python venv. Install [anaconda](https://www.anaconda.com/distribution/) and create a venv with
```console
conda create --name mqtt2timescale
```
If you are using [anaconda](https://www.anaconda.com/distribution/) the first time, you have to configure your shell, e.g. for git-bash
```console
conda init bash
```
2. Change to the venv with
```console
conda activate mqtt2timescale
```
3. Install the dependencies and run
```console
pip install -r requirements.txt
```

# Endpoints

### Health
[/api/health](localhost:8081/api/health)

# Environment
Take a look into .compose-envs mqtt2timescale.env
## Service Main Description
Descriptions important for the sidecar service and description generation
- *BASEPATH:* Basepath of the rest-api, e.g. /api
- *MAINCAR_HOST:* Address of the service, e.g. mqtt2timescale:1234
- *COMPOSITION_HOST:* Address of the composition-service, e.g. composition-service:8999
- *CONSUL_ADDRESS:* Address of the consul-service, e.g. composition_consul:8500
- *CONSUL_NAMESPACE:* Consul Namespace, e.g. PRODISYS
- *SERVICE_NAME:* Name of the service, e.g. mqtt2timescale-16.01.2020-20:11
- *DOCKER_IMAGE:* Name of the used dockerimage
- *TAGS:* Active Tags for this service: mqtt-client,timescaledb-client
- *LOCATION:* is this a external or internal application?
- *SERVICE_DESCRIPTION:* Long textual description of this service
## Mqtt-Client-Tag
All vars used to configure the mqtt-client tag:
- *MQTT_CLIENT_HOST:* Address of the mqtt-broker e.g. rabbitmq:1883
- *MQTT_CLIENT_TOPIC:* Name of the topic to be subscribed/pushed
- *MQTT_CLIENT_DIRECTION:* Direction of the connection, e.g subscribe or publishe
- *MQTT_CLIENT_PURPOSE:* Textual description of the purpose
- *MQTT_CLIENT_USERNAME:* Username to access the broker
- *MQTT_CLIENT_PASSWORD:* Password to access the broker
## Timescaledb-Client-Tag
- *TIMESCALEDB_HOST:* Address of the timescaledb server, e.g. timescaledb:1337
- *TIMESCALEDB_NAME:* Name of the used database, something like postgres or energy_db
- *TIMESCALEDB_USERNAME:* Username to access the db
- *TIMESCALEDB_PASSWORD:* Db user password
- *TIMESCALEDB_TABLE_NAME:* Name of the target table inside the db
- *TIMESCALEDB_REPLACE_EXISTING_TABLE:* true/false, if you want to replace the contents of an existing table or just append
- *TIMESCALEDB_INDEX_COLUMN:* Index column of the table, e.g. timestamp
- *TIMESCALEDB_CHUNKING_INTERVAL:* Interval to create data chunks, e.g. "1 hours"
- *TIMESCALEDB_DROP_CHUNK_AFTER:* Configure Data retendtion, e.g. "7 days" or "never"
- *TIMESCALEDB_COMPRESS_AFTER:* Define the time, after data is compressed, e.g. "6 hours"
- *TIMESCALEDB_HEADER_STRING:* Name of the columns, should be consistent with the mqtt-input, e.g. timestamp;val1;val2
- *TIMESCALEDB_DIRECTION:* Direction of the client connection, e.g. read/write
- *TIMESCALEDB_PURPOSE:* Textual description of the connection purpose
## Debug
- *DEBUG:* Activate pycharm python debugger (True/False)
- *DEBUG_ADDRESS:* Address of the pycharm debugger connection, e.g. 192.168.178.33