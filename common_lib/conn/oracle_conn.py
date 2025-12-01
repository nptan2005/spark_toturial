# common_lib/db/oracle_conn.py
from __future__ import annotations

import time
from typing import Any, List, Dict, Optional

import cx_Oracle
import pandas as pd
import pandas.io.sql as psql

from ..config_models import configuration, app_service_config
from .base_db import BaseDBConn


class OracleConn(BaseDBConn):
    def __init__(self, connection_name: str, time_out: int = None):
        BaseDBConn.__init__(self, connection_name, time_out)

        self._config = configuration.oracle_database[connection_name]
        self._dns = cx_Oracle.makedsn(
            self._config.host,
            self._config.port,
            service_name=self._config.service_name,
        )
        self._db_version: Optional[str] = None

    # ---------------- connection -----------------
    def _connect(self) -> None:
        try:
            self._conn = cx_Oracle.connect(
                user=self._config.username,
                password=self._config.password,
                dsn=self._dns,
                encoding="UTF-8",
                nencoding="UTF-8",
            )
            self._db_version = self._conn.version
        except Exception as e:
            self.logger.exception(f"[OracleConn.__enter__][{self.elapsed:.2f}s] Error: {e}")
            self._conn = None

    def is_connected(self) -> bool:
        if self._conn is None:
            return False
        try:
            self._conn.ping()
            return True
        except cx_Oracle.InterfaceError as e:
            self.logger.warning(f"[OracleConn.is_connected][{self.elapsed:.2f}s] {e}")
            return False
        except Exception as e:
            self.logger.warning(f"[OracleConn.is_connected][{self.elapsed:.2f}s] {e}")
            return False

    def close(self) -> None:
        try:
            if self._conn:
                self._conn.close()
                self.logger.info(f"[OracleConn.close][{self.elapsed:.2f}s] closed.")
        except Exception as e:
            self.logger.warning(f"[OracleConn.close][{self.elapsed:.2f}s] {e}")

    # ---------------- base API implement -----------------
    def execute(self, sql: str, params: Any = None):
        if not self.is_connected():
            self.logger.error(f"[OracleConn.execute][{self.elapsed:.2f}s] connection not open")
            self.err_msg = "Connection not open"
            return None

        with self._conn.cursor() as cur:
            try:
                cur.execute(sql, params or ())
                return cur
            except Exception as e:
                self.logger.exception(f"[OracleConn.execute][{self.elapsed:.2f}s] {e}")
                self.err_msg = str(e)
                return None

    def query_df(self, sql: str, params: Any = None) -> pd.DataFrame:
        if not self.is_connected():
            self.logger.error(f"[OracleConn.query_df][{self.elapsed:.2f}s] connection not open")
            self.err_msg = "Connection not open"
            return pd.DataFrame()

        with self._conn.cursor() as cur:
            try:
                cur.execute(sql, params or ())
                cols = [c[0] for c in cur.description]
                rows = cur.fetchall()
                return pd.DataFrame(rows, columns=cols)
            except Exception as e:
                self.logger.exception(f"[OracleConn.query_df][{self.elapsed:.2f}s] {e}")
                self.err_msg = str(e)
                return pd.DataFrame()

    def to_sql(self, df: pd.DataFrame, table_name: str, if_exists="replace", index=False) -> bool:
        # với Oracle qua cx_Oracle thì to_sql của pandas không xài thẳng được như SQLAlchemy
        # Nếu muốn dùng SQLAlchemy cho Oracle, có thể tạo engine riêng
        # Ở đây tạm raise NotImplementedError để Tân tự chọn chiến lược
        raise NotImplementedError("Implement to_sql cho Oracle bằng SQLAlchemy hoặc PL/SQL bulk insert.")