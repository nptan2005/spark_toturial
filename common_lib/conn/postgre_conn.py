# common_lib/db/postgre_conn.py
from __future__ import annotations

import time
from typing import Any, Union, List

import pandas as pd
from sqlalchemy import create_engine, text, bindparam
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.exc import OperationalError

from ..config_models import configuration
from .base_db import BaseDBConn


class PostgreConn(BaseDBConn):

    def __init__(self, connection_name: str, time_out: int | None = None):
        BaseDBConn.__init__(self, connection_name, time_out)

        self._config = configuration.postgre_database[connection_name]
        self.db_url = (
            f"postgresql://{self._config.username}:{self._config.password}"
            f"@{self._config.host}:{self._config.port}/{self._config.database}"
        )
        self.pool_size = 5
        self.max_overflow = 10
        self._engine = None

    # ---------------- connection -----------------
    def _connect(self) -> None:
        try:
            self._engine = create_engine(
                self.db_url,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_pre_ping=True,
            )
            self._conn = self._engine.connect()
        except OperationalError as e:
            self.logger.exception(f"[PostgreConn._connect][{self.elapsed:.2f}s] {e}")
            self._conn = None

    def is_connected(self) -> bool:
        return self._conn is not None and not self._conn.closed

    def close(self) -> None:
        try:
            if self._conn and not self._conn.closed:
                self._conn.close()
                self.logger.info(f"[PostgreConn.close][{self.elapsed:.2f}s] closed.")
        except Exception as e:
            self.logger.warning(f"[PostgreConn.close][{self.elapsed:.2f}s] {e}")

    # ---------------- base API implement -----------------
    def execute(self, sql: str, params: Any = None):
        if not self.is_connected():
            self.logger.error(f"[PostgreConn.execute][{self.elapsed:.2f}s] connection not open")
            self.err_msg = "Connection not open"
            return None
        self.logger.info(f"[PostgreConn.execute][{self.elapsed:.2f}s] SQL={sql}, params={params}")
        try:
            return self._conn.execute(text(sql), params or {})
        except Exception as e:
            self.logger.exception(f"[PostgreConn.execute][{self.elapsed:.2f}s] {e}")
            self.err_msg = str(e)
            return None

    def query_df(self, sql: str, params: Any = None) -> pd.DataFrame:
        if not self.is_connected():
            self.logger.error(f"[PostgreConn.query_df][{self.elapsed:.2f}s] connection not open")
            self.err_msg = "Connection not open"
            return pd.DataFrame()
        self.logger.info(f"[PostgreConn.query_df][{self.elapsed:.2f}s] SQL={sql}, params={params}")
        try:
            return pd.read_sql(sql, self._engine, params=params)
        except Exception as e:
            self.logger.exception(f"[PostgreConn.query_df][{self.elapsed:.2f}s] {e}")
            self.err_msg = str(e)
            return pd.DataFrame()

    def to_sql(self, df: pd.DataFrame, table_name: str, if_exists="replace", index=False) -> bool:
        if not self.is_connected():
            self.logger.error(f"[PostgreConn.to_sql][{self.elapsed:.2f}s] connection not open")
            return False
        self.logger.info(f"[PostgreConn.to_sql][{self.elapsed:.2f}s] table={table_name}")
        try:
            df.to_sql(table_name, self._engine, if_exists=if_exists, index=index)
            return True
        except Exception as e:
            self.logger.exception(f"[PostgreConn.to_sql][{self.elapsed:.2f}s] {e}")
            self.err_msg = str(e)
            return False