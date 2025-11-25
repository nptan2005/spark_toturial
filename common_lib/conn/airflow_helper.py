# common_lib/conn/airflow_helper.py
from typing import Literal

try:
    from airflow.hooks.base import BaseHook
except ImportError:
    BaseHook = None  # để code vẫn import được ngoài Airflow


def get_pg_config_from_airflow(conn_id: str):
    if BaseHook is None:
        raise RuntimeError("Airflow is not installed")

    conn = BaseHook.get_connection(conn_id)
    return {
        "host": conn.host,
        "port": conn.port,
        "database": conn.schema,
        "username": conn.login,
        "password": conn.password,
    }