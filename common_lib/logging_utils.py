import logging
import logging.config
import os
from pathlib import Path


CONFIG_PATH = Path(__file__).resolve().parent / "configurable" / "logging.conf"


def setup_logger(name: str = "APP"):
    """
    Load logging from config file if exists.
    Otherwise fallback to basic RotatingFileHandler logger.
    """

    # --- CASE 1: logging.conf exists → load fileConfig ---
    if CONFIG_PATH.exists():
        logging.config.fileConfig(CONFIG_PATH, disable_existing_loggers=False)
        logger = logging.getLogger(name)
        logger.info(f"[logging_utils] Loaded logging config from {CONFIG_PATH}")
        return logger

    # --- CASE 2: fallback default logger ---
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    log_dir = Path("Logs")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "app.log"

    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(lineno)04d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    logger.info("[logging_utils] Using default internal logger (fallback mode)")
    return logger