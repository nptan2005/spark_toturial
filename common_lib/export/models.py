# common_lib/export/models.py

from typing import Dict, Optional
from pydantic import BaseModel, Field, field_validator
from pathlib import Path
import yaml

from .constants import DataConstant


class SheetConfig(BaseModel):
    is_header: bool = Field(default=True)
    sheet_title_name: Optional[str] = Field("", description="Title of the sheet")
    sheet_name: Optional[str] = Field(default=None, description="Name of the sheet in Excel")
    is_format: bool = Field(default=False)
    column_mapping: Dict[str, str] = Field(default_factory=dict)

    @field_validator("is_header", "is_format", mode="before")
    def parse_bool(cls, v):
        if isinstance(v, str):
            return v.lower() in ["true", "1", "yes", "y"]
        return bool(v)


class ExportTemplate(BaseModel):
    file_extension: str = "xlsx"
    separate: str = "|"
    sftp_conn: Optional[str] = None
    sftp_move: bool = Field(default=True)
    sheets: Dict[str, SheetConfig]

    @field_validator("sftp_move", mode="before")
    def parse_bool(cls, v):
        if isinstance(v, str):
            return v.lower() in ["true", "1", "yes", "y"]
        return bool(v)


class ExportConfig(BaseModel):
    export_template: Dict[str, ExportTemplate]


# ---- Loader YAML ----

def load_export_config(config_path: str | Path) -> ExportConfig:
    """
    Load export_config.yaml và parse sang ExportConfig.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Export config not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return ExportConfig(**data)


def get_template(config: ExportConfig, template_key: str | None):
    """
    Lấy template theo key; nếu không có thì dùng DEFAULT.
    """
    if not template_key:
        template_key = DataConstant.DEFAULT

    tpl = config.export_template.get(template_key)
    if not tpl:
        # fallback về DEFAULT
        tpl = config.export_template[DataConstant.DEFAULT]
    return tpl