# common_lib/import_/models.py

from typing import Dict, List, Optional
import os

from pydantic import BaseModel, Field, field_validator

from common_lib.config_utils import ConfigUtils  # nếu anh đang để ConfigUtils ở nơi khác thì chỉnh lại import

class _ETLConfig(BaseModel):
    load_type: str = Field(default="Full")  # or "Incremental"
    source_conn_str: Optional[str] = None
    target_table: Optional[str] = None
    key_columns: Optional[List[str]] = None
    where_condition: Optional[str] = None


class _ImportTemplate(BaseModel):
    header: Optional[List[str]] = None
    import_type: str = "File"  # or "Database"
    etl: Optional[_ETLConfig] = None

    file_extension: str = "xlsx"
    file_encoding: Optional[str] = None
    separate: Optional[str] = "|"

    sftp_conn: Optional[str] = None
    sftp_move: bool = False

    start_row: int = 2
    end_row: Optional[int] = 0
    start_col: int = 1
    end_col: Optional[int] = 0
    is_read_to_empty_row: bool = False

    table_name: str
    is_truncate_tmp_table: bool = False
    procedure_name: Optional[str] = None
    external_process: Optional[str] = None
    column_mapping: Optional[Dict[str, str]] = None

    @field_validator('sftp_move', 'is_read_to_empty_row', 'is_truncate_tmp_table', mode='before')
    def parse_bool(cls, v):
        if isinstance(v, str):
            return v.lower() in ['true', '1', 'yes']
        return bool(v)


class _ImportConfig(BaseModel):
    import_template: Dict[str, _ImportTemplate]

    def __init__(self, **data):
        ConfigUtils.check_import()
        super().__init__(**data)


# load global config
_import_config_path = os.path.join("common_lib", "configurable", "import_config.yaml")
import_configuration: _ImportConfig = ConfigUtils.load_config(_import_config_path, _ImportConfig)