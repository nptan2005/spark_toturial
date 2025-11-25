# common_lib/export/exporter.py

from __future__ import annotations

from typing import Dict, List, Optional, Sequence
from pathlib import Path
import inspect

import numpy as np
import pandas as pd
import xlsxwriter

from .constants import DataConstant
from .models import ExportConfig, ExportTemplate, SheetConfig, get_template
from common_lib.logging_utils import setup_logger


class DataExporter:
    """
    Class export đa năng (Excel/CSV/JSON/Text) dùng template YAML.

    export_data: list[pd.DataFrame]
    export_name: list[str]  # key trong template.sheets
    """

    def __init__(
        self,
        export_data: Sequence[pd.DataFrame],
        export_name: Sequence[str],
        file_name: str,
        template_key: Optional[str],
        export_config: ExportConfig,
        file_extension: str = "xlsx",
        logger_name: str = "EXPORT",
    ):
        self.logger = setup_logger(logger_name)

        self._config = export_config
        self._template: ExportTemplate = get_template(self._config, template_key)

        # nếu template có file_extension thì ưu tiên, nếu không dùng tham số truyền vào
        self._file_type = self._template.file_extension or file_extension

        self._file_name = file_name
        self._sep = self._template.separate

        self._export_data: List[pd.DataFrame] = list(export_data)
        self._export_name: List[str] = list(export_name)

        self._is_successful = False
        self._note = ""
        self._title = ""

    # ========= context manager support =========
    def __enter__(self) -> "DataExporter":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._clear_attributes()

    def __del__(self):
        self._clear_attributes()

    def _clear_attributes(self):
        attrs = [
            "_file_name",
            "_file_type",
            "_sep",
            "_export_data",
            "_export_name",
            "_is_successful",
            "_note",
            "_template",
            "_config",
            "_title",
            "logger",
        ]
        for a in attrs:
            if hasattr(self, a):
                setattr(self, a, None)

    # ========= helper lấy config sheet =========

    def get_sheet_config(self, key: str) -> Optional[SheetConfig]:
        return self._template.sheets.get(key)

    def get_sheet_name(self, key: str) -> Optional[str]:
        cfg = self.get_sheet_config(key)
        return cfg.sheet_name if cfg and cfg.sheet_name else key

    def get_sheet_title_name(self, key: str) -> Optional[str]:
        cfg = self.get_sheet_config(key)
        return cfg.sheet_title_name if cfg else None

    def get_sheet_is_header(self, key: str) -> bool:
        cfg = self.get_sheet_config(key)
        return cfg.is_header if cfg else True

    def get_sheet_is_format(self, key: str) -> bool:
        cfg = self.get_sheet_config(key)
        return cfg.is_format if cfg else False

    # ========= transform header / column mapping =========

    def _apply_header_config(
        self, df: pd.DataFrame, header_config: Optional[Dict[str, str]]
    ) -> pd.DataFrame:
        if header_config and isinstance(header_config, dict):
            rename_dict = {col: header_config.get(col, col) for col in df.columns}
            df = df.rename(columns=rename_dict)
        return df

    def _data_export_dict(self) -> Dict[str, pd.DataFrame]:
        """
        Từ list export_data + export_name => dict key -> df (đã apply column_mapping).
        """
        data_dict: Dict[str, pd.DataFrame] = {}

        for idx, key in enumerate(self._export_name):
            try:
                if 0 <= idx < len(self._export_data):
                    df = self._export_data[idx]
                    cfg = self.get_sheet_config(key)
                    if cfg and cfg.column_mapping:
                        df = self._apply_header_config(df, cfg.column_mapping)
                    self._export_data[idx] = df
                    data_dict[key] = df
            except Exception as e:
                fn = inspect.currentframe().f_code.co_name
                self._note += (
                    f"[{self.__class__.__name__}][{fn}] "
                    f"Transform data for key {key} encountered an error\n"
                )
                self.logger.exception(
                    f"Transform data for key {key} encountered an error: {e}"
                )

        return data_dict

    # ========= properties =========

    @property
    def export_data(self) -> List[pd.DataFrame]:
        return self._export_data

    @property
    def export_name(self) -> List[str]:
        return self._export_name

    @property
    def file_type(self) -> str:
        return self._file_type

    @property
    def file_name(self) -> str:
        return self._file_name

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str):
        self._title = value

    @property
    def is_successful(self) -> bool:
        return self._is_successful

    @property
    def note(self) -> str:
        return self._note.strip()

    # ========= Excel export =========

    def _export_to_excel(self):
        if not self._has_data():
            self.logger.info("==> Data empty => Not export file")
            self._is_successful = True
            return

        if self._invalid_multi_sheet_mapping():
            self.logger.info(
                "==> Config incorrect - Sheet array None or not map Data => Not export"
            )
            return

        export_data_dict = self._data_export_dict()

        try:
            file_name = f"{self.file_name}.{self.file_type}"
            path = Path(file_name)

            with pd.ExcelWriter(
                path,
                engine="xlsxwriter",
                datetime_format="dd/mm/yyyy hh:mm:ss",
                date_format="dd/mm/yyyy",
            ) as writer:
                workbook = writer.book

                for key in self._export_name:
                    df = export_data_dict.get(key)
                    if df is None:
                        self.logger.info(
                            f"==> Sheet Name [{key}] not found in data dictionary."
                        )
                        continue

                    if df.shape[0] == 0 or df.shape[1] == 0:
                        self.logger.info(
                            f"==> Sheet Name [{key}]: Data empty => not create sheet"
                        )
                        continue

                    sheet_name = self.get_sheet_name(key)
                    if not sheet_name:
                        self.logger.info(
                            f"==> Sheet name for key [{key}] is None, skipping sheet."
                        )
                        continue

                    sheet_title = self.get_sheet_title_name(key)
                    start_row = 0
                    freeze = 1
                    if sheet_title:
                        start_row = 1
                        freeze += start_row

                    # write data
                    df.to_excel(
                        writer, sheet_name=sheet_name, startrow=start_row, index=False
                    )
                    worksheet = writer.sheets[sheet_name]
                    worksheet.freeze_panes(freeze, 1)

                    # title row
                    if sheet_title:
                        title_format = workbook.add_format(
                            {
                                "bold": True,
                                "font_size": 13,
                                "align": "center",
                                "valign": "vcenter",
                                "fg_color": "#c1e8c1",
                                "font_color": "#0b3601",
                            }
                        )
                        worksheet.merge_range(
                            0, 0, 0, len(df.columns) - 1, sheet_title, title_format
                        )

                    # header format
                    if self.get_sheet_is_header(key):
                        header_format = workbook.add_format(
                            {
                                "bold": True,
                                "font_size": 12,
                                "text_wrap": True,
                                "valign": "center",
                                "fg_color": "#E0F7E0",
                                "font_color": "#0b3601",
                                "border": 1,
                            }
                        )
                        for col_num, value in enumerate(df.columns):
                            worksheet.write(start_row, col_num, value, header_format)

                    # row format
                    if self.get_sheet_is_format(key):
                        self._apply_row_formatting(df, worksheet, start_row, workbook)

                    self.logger.info(
                        f"==> Sheet Name [{key}] => Data counter: {df.shape[0]}"
                    )

            self._is_successful = True
        except Exception as e:
            self._is_successful = False
            fn = inspect.currentframe().f_code.co_name
            self._note += (
                f"==> File Name {self.file_name}.{self.file_type} "
                f"[{self.__class__.__name__}][{fn}] Process with Error\n"
            )
            self.logger.exception(e)

    def _apply_row_formatting(
        self,
        df: pd.DataFrame,
        worksheet: "xlsxwriter.worksheet.Worksheet",
        start_row: int,
        workbook: "xlsxwriter.workbook.Workbook",
    ):
        even_row_format = workbook.add_format(
            {"bg_color": "#FFFFFF", "border": 1, "font_size": 11}
        )
        odd_row_format = workbook.add_format(
            {"bg_color": "#d4fcf5", "border": 1, "font_size": 11}
        )

        even_date_format = workbook.add_format(
            {
                "num_format": "dd/mm/yyyy",
                "bg_color": "#FFFFFF",
                "font_size": 11,
                "border": 1,
            }
        )
        odd_date_format = workbook.add_format(
            {
                "num_format": "dd/mm/yyyy",
                "bg_color": "#d4fcf5",
                "font_size": 11,
                "border": 1,
            }
        )
        even_datetime_format = workbook.add_format(
            {
                "num_format": "dd/mm/yyyy hh:mm:ss",
                "bg_color": "#FFFFFF",
                "font_size": 11,
                "border": 1,
            }
        )
        odd_datetime_format = workbook.add_format(
            {
                "num_format": "dd/mm/yyyy hh:mm:ss",
                "bg_color": "#d4fcf5",
                "font_size": 11,
                "border": 1,
            }
        )

        for index, row in df.iterrows():
            row = row.replace([np.inf, -np.inf], np.nan).fillna("")
            row_fmt = even_row_format if index % 2 == 0 else odd_row_format
            date_fmt = even_date_format if index % 2 == 0 else odd_date_format
            datetime_fmt = (
                even_datetime_format if index % 2 == 0 else odd_datetime_format
            )

            for col_num, cell_data in enumerate(row):
                col_series = df.iloc[:, col_num]
                if pd.api.types.is_datetime64_any_dtype(col_series):
                    # phân biệt date vs datetime nếu cần
                    fmt = datetime_fmt if col_series.dtype == "datetime64[ns]" else date_fmt
                    worksheet.write(index + start_row + 1, col_num, cell_data, fmt)
                else:
                    worksheet.write(index + start_row + 1, col_num, cell_data, row_fmt)

        # autosize columns
        for col_num, value in enumerate(df.columns):
            column_len = max(
                df[value].astype(str).map(len).max(), len(value)
            ) + 2
            worksheet.set_column(col_num, col_num, column_len)

    # ========= CSV / TEXT / JSON =========

    def _export_to_csv(self):
        if not self._has_data():
            self.logger.info("==> Data empty => Not export file")
            self._is_successful = True
            return

        if self._invalid_multi_sheet_mapping():
            self.logger.info(
                "==> Config incorrect - Array None or not map Data => Not export file"
            )
            return

        try:
            for i, df in enumerate(self.export_data):
                key = self.export_name[i]
                num = f"_{i}" if i > 0 else ""
                file_name = f"{self.file_name}{num}_{key}.{self.file_type}"
                path = Path(file_name)
                is_header = self.get_sheet_is_header(key)

                if df is not None and df.shape[0] > 0 and df.shape[1] > 0:
                    df.to_csv(
                        path,
                        sep=self._sep,
                        index=False,
                        header=is_header,
                        encoding="utf-8",
                    )
                    self.logger.info(
                        f"==> Data [{i}] {key} => Data counter: {df.shape[0]}"
                    )
                else:
                    self.logger.info(
                        f"==> Data [{i}] {key}: empty => Not create file"
                    )
            self._is_successful = True
        except Exception as e:
            self._is_successful = False
            fn = inspect.currentframe().f_code.co_name
            self._note += (
                f"==> File export [{self.__class__.__name__}][{fn}] Process with Error\n"
            )
            self.logger.exception(e)

    def _export_to_any_file(self):
        if not self._has_data():
            self.logger.info("==> Data empty => Not export file")
            self._is_successful = True
            return

        if self._invalid_multi_sheet_mapping():
            self.logger.info(
                "==> Config incorrect - Array None or not map Data => Not export file"
            )
            return

        try:
            for i, df in enumerate(self.export_data):
                key = self.export_name[i]
                num = f"_{i}" if i > 0 and df is not None else ""
                file_name = f"{self.file_name}{num}_{key}.{self.file_type}"
                path = Path(file_name)

                if df is not None and df.shape[0] > 0 and df.shape[1] > 0:
                    self._data_frame_export(df, self.file_type, path)
                    self.logger.info(
                        f"==> Data [{i}] {key} => Data counter: {df.shape[0]}"
                    )
                else:
                    self.logger.info(
                        f"==> Data [{i}] {key}: empty => Not create file"
                    )
            self._is_successful = True
        except Exception as e:
            self._is_successful = False
            fn = inspect.currentframe().f_code.co_name
            self._note += (
                f"==> File export [{self.__class__.__name__}][{fn}] Process with Error\n"
            )
            self.logger.exception(e)

    def _data_frame_export(self, data: pd.DataFrame, file_format: str, file_path: Path):
        fmt = file_format.lower()
        if fmt == DataConstant.RPT_CSV_FILE_TYPE:
            data.to_csv(
                file_path,
                sep=self._sep,
                index=False,
                header=True,
                encoding="utf-8",
            )
        elif fmt == DataConstant.RPT_TEXT_FILE_TYPE:
            data.to_csv(
                file_path,
                sep=self._sep,
                index=False,
                header=False,
                encoding="utf-8",
            )
        elif fmt == DataConstant.RPT_EXCEL_FILE_TYPE:
            data.to_excel(file_path, index=False)
        elif fmt == DataConstant.RPT_JSON_FILE_TYPE:
            data.to_json(file_path, orient="records", lines=True)
        else:
            data.to_csv(
                file_path,
                sep=self._sep,
                index=False,
                header=False,
                encoding="utf-8",
            )

    # ========= public API =========

    def to_file(self):
        """
        Export DataFrame theo định dạng:
          - Nếu file_type = xlsx => Excel (nhiều sheet, format)
          - Nếu csv => _export_to_csv
          - Khác => _export_to_any_file
        """
        try:
            if self.file_type == DataConstant.RPT_EXCEL_FILE_TYPE:
                self._export_to_excel()
            elif self.file_type == DataConstant.RPT_CSV_FILE_TYPE:
                self._export_to_csv()
            else:
                self._export_to_any_file()
        except Exception as e:
            self._is_successful = False
            fn = inspect.currentframe().f_code.co_name
            self._note += f"[{self.__class__.__name__}][{fn}] Error\n"
            self.logger.exception(e)

    # ========= internal checks =========

    def _has_data(self) -> bool:
        return bool(self.export_data) and not (
            len(self.export_data) == 1 and self.export_data[0].shape[0] == 0
        )

    def _invalid_multi_sheet_mapping(self) -> bool:
        return len(self.export_data) > 1 and (
            not self.export_name
            or len(self.export_data) != len(self.export_name)
        )