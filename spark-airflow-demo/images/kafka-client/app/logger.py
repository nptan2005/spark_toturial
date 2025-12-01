import sys
from loguru import logger

logger.add("/app/logs/producer.log", rotation="10 MB", retention="7 days")
logger.add(sys.stdout, level="INFO")
