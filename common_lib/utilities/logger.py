import logging
import logging.config
from logging.handlers import RotatingFileHandler
import datetime
import os

class Logger:

    _instance = None

    _path_log_config = None
    _objName = None
    _logger = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, objName:str = 'BVB'):

        self._objName = objName
        self.isUseConfigLogFile = True
        self._path_log_config = os.path.join("configurable","logging.conf")

        self._logger = logging.getLogger(self._objName)
        logging.config.fileConfig(self._path_log_config,disable_existing_loggers=False)

        self._logger.addFilter(ErrorFilter())


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._logger = None

    def __del__(self):
        del self._objName, self._path_log_config

    @property
    def isExistsLoggerConfig(self) -> bool:
        return os.path.exists(self._path_log_config)
    @property
    def logConfigPath(self):
       return self._path_log_config

    def get_log_file_path(self,max_bytes = 2 * 1024 * 1024, backup_count = 5):
        """Tạo đường dẫn đến file log dựa trên file config."""
        log_dir = '..' + os.path.sep + 'Logs'
        log_dir.mkdir(parents=True, exist_ok=True)  # Tạo thư mục nếu chưa tồn tại
        today = datetime.date.today().strftime("%Y%m%d")  # Lấy ngày hiện tại theo định dạng yyyymmdd

        return log_dir + os.path.sep + f"{today}.log"

    def setup_logger(self,max_bytes = 2 * 1024 * 1024, backup_count = 5):
        """Cấu hình logger."""
        # Lấy logger hiện tại
        logger = logging.getLogger(self._objName)
        
        # Xóa tất cả các handler cũ
        if logger.hasHandlers():
            logger.handlers.clear()

        log_file_path = self.get_log_file_path()
        handler = RotatingFileHandler(
            log_file_path, maxBytes=max_bytes, backupCount=backup_count
        )
        formatter = logging.Formatter(
            "%(asctime)s | %(name)-16s | %(levelname)-8s | %(lineno)04d | %(message)s"
        )
        handler.setFormatter(formatter)

        logger = logging.getLogger(__name__)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)  # Cấu hình mức độ log mặc định là INFO
        return logger

    @property
    def logger(self):
        return self._logger
    
    @property
    def logName(self):
        return self._objName
    
    @logName.setter
    def logName(self,value):
        self._objName = value
        self._logger = logging.getLogger(self._objName)

    

class ErrorFilter(logging.Filter):
    def filter(self, record):
        # When log level is ERROR or CRITICAL, update handler format
        if record.levelno >= logging.ERROR:
            for handler in logging.getLogger().handlers:
                if isinstance(handler, RotatingFileHandler):
                    handler.setFormatter(logging.Formatter(
                        "%(asctime)s | %(name)-16s | %(levelname)-8s | %(module)s.%(funcName)s-%(lineno)04d | %(message)s"
                    ))
        return True



