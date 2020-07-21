from utils.typesafe_dataclass import TypesafeDataclass
from typing import List, Dict, Tuple, Sequence


class Mqtt2TimescaleEnvironment(TypesafeDataclass):
    # Defaults with type
    maincar_host: str = "mqtt2timescale:8081"
    composition_host: str = "composition-service:8999"
    consul_address: str = "composition_consul:8500"
    consul_namespace: str = "PRODISYS"
    service_name: str = "mqtt2timecale-~forgott-to-set-name~"

    # Mqtt-Client-Tag
    mqtt_client_host: str = "rmq-mqtt:1883"
    mqtt_client_topic: str = "test"
    mqtt_client_direction: str = "subscriber"
    mqtt_client_purpose: str = ""
    # Mqtt-Client-Secrets
    mqtt_client_username: str = "mqtt2timescale"
    mqtt_client_password: str = "m2t_321"

    # Timescaledb-Client-Tag
    timescaledb_host: str = "timescale:5432"
    timescaledb_name: str = "postgres"
    timescaledb_table_name: str = "test_table"
    timescaledb_replace_existing_table: bool = False
    timescaledb_index_column: str = "timestamp"
    timescaledb_chunking_interval: str = "1 hours"
    timescaledb_drop_chunk_after: str = "never"
    timescaledb_compress_after: str = "6 hours"
    timescaledb_header_string: str = "id;power_1;power_2;power_3;phaseshift_1;phaseshift_2;phaseshift_3;current_1;current_2;current_3;voltage_1;voltage_2;voltage_3;deviation_1;deviation_2;deviation_3;unix_timestamp;timestamp"
    timescaledb_direction: str = "write"
    timescaledb_purpose: str = ""
    # Timescaledb-Client-Secrets
    timescaledb_username: str = "mqtt2timescale"
    timescaledb_password: str = "fortiss123"

    # Debug
    debug: bool = False
    debug_address: str = "192.168.178.33"

    def __init__(self):
        super().__init__()
