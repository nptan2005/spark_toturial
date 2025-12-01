import pytest
from unittest.mock import MagicMock


@pytest.fixture(autouse=True)
def mock_logger(monkeypatch):
    fake_logger = MagicMock()
    monkeypatch.setattr(
        "common_lib.logging_utils.setup_logger",
        lambda name="APP": fake_logger
    )
    return fake_logger

@pytest.fixture(autouse=True)
def mock_read_file(monkeypatch):
    monkeypatch.setattr(
        "common_lib.config_utils.ConfigUtils.read_file",
        lambda *_args, **_kwargs: "<html>mock</html>"
    )

