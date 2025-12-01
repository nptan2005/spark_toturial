import os
import base64
import threading
from typing import Dict, Optional, List
from pathlib import Path
import yaml
from pydantic import BaseModel, Field, EmailStr, field_validator

from .config_utils import ConfigUtils
from .importer.models import import_configuration
from .multiAlgoCoder import EncryptionManager

_manager = EncryptionManager()

# ----------------------------
# BUILD ABSOLUTE PATHS
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent


# ----------------------------------------------------------
# Oracle
# ----------------------------------------------------------
class OrlDatabaseConfig(BaseModel):
    host: str
    port: int
    service_name: str
    username: str
    password: str
    tns: str

    @field_validator("password", mode="before")
    def decode_password(cls, value):
        raw = base64.b64decode(value).decode()
        return _manager.decrypt(raw)


# ----------------------------------------------------------
# PostgreSQL
# ----------------------------------------------------------
class PostgreConfig(BaseModel):
    host: str
    port: int
    database: str
    username: str
    password: str

    @field_validator("password", mode="before")
    def decode_password(cls, value):
        raw = base64.b64decode(value).decode()
        return _manager.decrypt(raw)


# ----------------------------------------------------------
# Email config
# ----------------------------------------------------------
class EmailConfig(BaseModel):
    host: str
    port: int
    email: str
    password: str
    mail_list: Optional[List[EmailStr]] = None
    is_ssl: bool = True
    password_authen: bool = True
    is_debug: bool = True

    @field_validator("password", mode="before")
    def decode_password(cls, value):
        raw = base64.b64decode(value).decode()
        return _manager.decrypt(raw)

    @field_validator("is_ssl", "password_authen", "is_debug", mode="before")
    def parse_bool(cls, v):
        if isinstance(v, str):
            return v.lower() in ["true", "1", "yes"]
        return bool(v)


# ----------------------------------------------------------
# File Path
# ----------------------------------------------------------
class FilePath(BaseModel):
    root: str
    path: str
    file: Optional[str] = None
    full_path: Optional[str] = None
    _file_content: Optional[str] = None

    def model_post_init(self, __ctx__):
        base = BASE_DIR / self.root / self.path
        if self.file:
            self.full_path = str(base / self.file) if self.file else str(base)
        else:
            self.full_path = base

        self._file_content = self._read()

    def _read(self):
        if self.file:
            return ConfigUtils.read_file(self.full_path, "r")
        return None

    @property
    def file_content(self):
        if not self._file_content:
            self._file_content = self._read()
        return self._file_content


# ----------------------------------------------------------
# AppConfig root
# ----------------------------------------------------------
class AppConfig(BaseModel):
    oracle_database: Dict[str, OrlDatabaseConfig]
    postgre_database: Dict[str, PostgreConfig]
    email: Dict[str, EmailConfig]
    file_path: Dict[str, FilePath]
    sftp: Dict[str, dict]


# ----------------------------------------------------------
# Singleton loader
# ----------------------------------------------------------
class AppConfigSingleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, config_path: str):
        with cls._lock:
            if cls._instance is None:
                with open(config_path, "r") as f:
                    data = yaml.safe_load(f)
                cls._instance = AppConfig(**data)
        return cls._instance


# Tự load config.yaml
# app_config_path = BASE_DIR / "configurable" / "config.yaml"
# configuration = AppConfigSingleton(str(app_config_path))

# ----------------------------------------------------------
# App Service Config
# ----------------------------------------------------------
class EnvConfig(BaseModel):
    config_cycle_time: int
    config_sleep_time: int
    service_temporary_stop: bool
    service_running: bool
    is_email_summary: bool
    task_prc: str
    his_prc: str
    import_log_prc: str
    import_status_prc: str
    orl_sys_tbl_col: str
    orl_sys_tbl_tbl: str
    default_orl_db_conn: str
    default_sftp_conn: str
    default_email_conn: str
    email_template: str
    default_imp_key: str
    default_exp_key: str
    default_attchment_path: str
    default_archive_path: str
    default_archive_sftp: str
    default_archive_imp: str
    default_ext_module: str

    @field_validator("service_running", "service_temporary_stop", "is_email_summary", mode="before")
    def parse_bool(cls, v):
        if isinstance(v, str):
            return v.lower() in ["true", "1", "yes"]
        return bool(v)


class AppEnvConfig(BaseModel):
    env: str
    UAT: Optional[EnvConfig] = None
    PROD: Optional[EnvConfig] = None

    def get_env(self):
        cfg = getattr(self, self.env, None)
        if not cfg:
            raise ValueError(f"environment config '{self.env}' not found")
        return cfg

def load_env_config():
    path = BASE_DIR / "configurable" / "appconfig.yaml"
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return AppEnvConfig(**data).get_env()


app_config_path = BASE_DIR / "configurable" / "config.yaml"
configuration = AppConfigSingleton(str(app_config_path))
app_service_config = load_env_config()
