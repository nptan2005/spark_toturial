# common_lib/conn/spark_helper.py
from ..config_models import configuration


def build_oracle_jdbc(connection_name: str) -> tuple[str, dict]:
    cfg = configuration.oracle_database[connection_name]
    url = f"jdbc:oracle:thin:@//{cfg.host}:{cfg.port}/{cfg.service_name}"
    props = {
        "user": cfg.username,
        "password": cfg.password,
        "driver": "oracle.jdbc.OracleDriver",
    }
    return url, props


def build_postgres_jdbc(connection_name: str) -> tuple[str, dict]:
    cfg = configuration.postgre_database[connection_name]
    url = f"jdbc:postgresql://{cfg.host}:{cfg.port}/{cfg.database}"
    props = {
        "user": cfg.username,
        "password": cfg.password,
        "driver": "org.postgresql.Driver",
    }
    return url, props