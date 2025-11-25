import os
from pathlib import Path
import logging
from unittest.mock import patch, MagicMock
from common_lib.logging_utils import setup_logger, CONFIG_PATH


def test_logging_loads_from_config(tmp_path, monkeypatch):
    """
    When logging.conf exists → must call logging.config.fileConfig
    """

    # Tạo file logging.conf giả
    conf_file = tmp_path / "logging.conf"
    conf_file.write_text("""
[loggers]
keys=root

[handlers]
keys=console

[formatters]
keys=default

[logger_root]
level=INFO
handlers=console

[handler_console]
class=StreamHandler
level=INFO
formatter=default
args=(sys.stdout,)

[formatter_default]
format=%(asctime)s | %(levelname)s | %(message)s
""")

    # Monkeypatch CONFIG_PATH để trỏ tới file giả
    monkeypatch.setattr("common_lib.logging_utils.CONFIG_PATH", conf_file)

    with patch("logging.config.fileConfig") as mock_fileConfig:
        logger = setup_logger("TEST")

        mock_fileConfig.assert_called_once()  # Xác nhận đã load config
        assert logger.name == "TEST"


def test_logging_fallback(monkeypatch):
    """
    When logging.conf missing → use fallback internal logger
    """

    # ép CONFIG_PATH thành file không tồn tại
    monkeypatch.setattr("common_lib.logging_utils.CONFIG_PATH", Path("/non/exist/file"))

    logger = setup_logger("TEST2")

    # Không gọi fileConfig
    # nên checking nếu handler là RotatingFileHandler
    assert any(
        isinstance(h, logging.handlers.RotatingFileHandler) for h in logger.handlers
    )

    # Check log fallback message
    logger.info("dummy")
    # không assertion khó → nhưng đoạn này test handler OK là đủ