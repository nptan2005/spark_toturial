# common_lib/db/base_db.py
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Optional

import pandas as pd

from ..logging_utils import setup_logger


class BaseDBConn(ABC):
    """
    Base abstraction cho mọi DB:
    - quản lý logger, timing
    - context manager
    - interface execute/query/to_sql
    """

    def __init__(self, connection_name: str, time_out: Optional[int] = None):
        self._connection_name = connection_name
        self._time_out = time_out
        self.logger = setup_logger("DB_CONN")
        self._conn = None
        self._error_msg: Optional[str] = None
        self.start_time = time.time()
        self._elapsed = 0.0

    # ----------------- context manager -----------------
    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        self._clear_attributes()

    def __del__(self):
        self._clear_attributes()

    def _clear_attributes(self):
        attrs = [
            "_connection_name", "_time_out", "logger",
            "_conn", "_error_msg", "start_time", "_elapsed",
        ]
        for a in attrs:
            setattr(self, a, None)

    # ----------------- timing -----------------
    @property
    def elapsed(self) -> float:
        self._elapsed = time.time() - self.start_time
        return self._elapsed

    # ----------------- abstract phần connection -----------------
    @abstractmethod
    def _connect(self) -> None:
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    # ----------------- common API -----------------
    @property
    def connection(self):
        return self._conn

    @property
    def err_msg(self) -> Optional[str]:
        return self._error_msg

    @err_msg.setter
    def err_msg(self, value: str):
        self._error_msg = value

    @abstractmethod
    def execute(self, sql: str, params: Any = None):
        """Execute không quan tâm kết quả (INSERT/UPDATE/DELETE)."""
        ...

    @abstractmethod
    def query_df(self, sql: str, params: Any = None) -> pd.DataFrame:
        """Query về DataFrame."""
        ...

    @abstractmethod
    def to_sql(self, df: pd.DataFrame, table_name: str, if_exists="replace", index=False) -> bool:
        """Đẩy DataFrame vào table."""
        ...