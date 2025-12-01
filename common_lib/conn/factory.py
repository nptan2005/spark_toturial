from typing import Literal

from .oracle_conn import OracleConn
from .postgre_conn import PostgreConn
from .base_db import BaseDBConn

DBType = Literal["oracle", "postgres"]


def get_db_conn(db_type: DBType, connection_name: str) -> BaseDBConn:
    if db_type == "oracle":
        return OracleConn(connection_name)
    elif db_type == "postgres":
        return PostgreConn(connection_name)
    else:
        raise ValueError(f"Unsupported db_type: {db_type}")