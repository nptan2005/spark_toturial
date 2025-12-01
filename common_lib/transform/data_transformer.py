import os
import re
import time
import unicodedata
from decimal import Decimal
from datetime import datetime
import pandas as pd

from common_lib.importer.models import import_configuration
from common_lib.logging_utils import setup_logger


class DataTransformer:
    """
    Chuẩn hóa toàn bộ Transform step:
    - Mapping header
    - Date/datetime normalization
    - NUMBER precision/scale
    - VARCHAR2 uppercase + remove accents
    - NUMBER <-> VARCHAR smart convert
    - Duplicate key filtering (incremental)
    """

    def __init__(self, template_name: str):

        self._template = import_configuration.import_template[template_name]
        self._sep = self._template.separate
        self._process_name = template_name

        self._is_incremental = (
            self._template.etl and self._template.etl.load_type == "Incremental"
        )
        self._is_file = self._template.import_type == "File"
        self._key_columns = (
            self._template.etl.key_columns if self._template.etl else None
        )

        self._note = ""
        self.logger = setup_logger("TRANSFORM")

    # ------------------------------------------------------
    # Context manager
    # ------------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.logger.info("[DataTransformer] Exiting transform context")
        self._clear()

    def __del__(self):
        self._clear()

    def _clear(self):
        for attr in [
            "_note", "_sep", "_is_incremental",
            "_process_name", "_template", "_is_file",
            "_key_columns", "logger"
        ]:
            setattr(self, attr, None)

    # ------------------------------------------------------
    # Properties
    # ------------------------------------------------------

    @property
    def template(self):
        return self._template

    @property
    def process_name(self):
        return self._process_name

    # ------------------------------------------------------
    # Core Oracle Transform
    # ------------------------------------------------------

    def prepare_oracle_df(self, df_schema: pd.DataFrame, df_imp: pd.DataFrame) -> pd.DataFrame:
        """
        Chuẩn hóa DataFrame theo schema của Oracle:
        - Clean NULL
        - Mapping header
        - Convert dtype theo NUMBER/VARCHAR2/DATE rules
        """
        start_time = time.time()

        # Step 1 – nếu import từ file thì FileImport đã xử lý NULL rồi
        if not self._is_file:
            df_imp = df_imp.map(self.replace_none_with_null)
            df_imp = self.df_replace_header(df_imp)

        # Duplicate detection
        dup = df_imp.columns[df_imp.columns.duplicated()]
        if not dup.empty:
            raise ValueError(f"Duplicate column detected: {dup.tolist()}")

        # Conversion map
        dtype_map = {
            ('VARCHAR2', 'datetime64'): lambda col, p, s, m:
                col.dt.strftime('%Y%m%d%H%M%S').str.slice(0, m),

            ('DATE', 'numeric'): lambda col, p, s, m:
                self.convert_to_datetime(col),

            ('DATE', 'str'): lambda col, p, s, m:
                self.convert_to_datetime(col),

            ('VARCHAR2', 'str'): lambda col, p, s, m:
                col.astype(str).apply(self.remove_vietnamese_accents).str.slice(0, m),

            ('VARCHAR2', 'bool'): lambda col, p, s, m:
                col.astype(str),

            ('NUMBER', 'bool'): lambda col, p, s, m:
                self.convert_bool_to_value(col, 'NUMBER'),

            ('VARCHAR2', 'numeric'): lambda col, p, s, m:
                self.convert_number_to_str(col, m),

            ('NUMBER', 'numeric'): lambda col, p, s, m:
                self.convert_number_dtype(col, p, s),

            ('NUMBER', 'str'): lambda col, p, s, m:
                self.convert_str_to_number(self.normalize_column(col), p, s),
        }

        for idx, row in df_schema.iterrows():

            col = row["COLUMN_NAME"]
            if col not in df_imp.columns:
                continue

            db_type = row["DATA_TYPE"]
            precision = int(row["PRECISION"]) if not pd.isna(row["PRECISION"]) else None
            scale = int(row["SCALE"]) if not pd.isna(row["SCALE"]) else None
            max_len = int(row["MAX_LENGTH"]) if not pd.isna(row["MAX_LENGTH"]) else None

            col_data = df_imp[col]

            if pd.api.types.is_numeric_dtype(col_data):
                dtype_cat = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                dtype_cat = "datetime64"
            elif pd.api.types.is_bool_dtype(col_data):
                dtype_cat = "bool"
            else:
                dtype_cat = "str"

            conv_key = (db_type, dtype_cat)
            fn = dtype_map.get(conv_key)

            try:
                if fn:
                    df_imp[col] = fn(col_data, precision, scale, max_len)
                else:
                    df_imp[col] = self.convert_dtype(col_data, db_type)

            except Exception as e:
                raise ValueError(
                    f"[prepare_oracle_df] Error converting column {col}: dtype={dtype_cat}, "
                    f"dbType={db_type}, precision={precision}, scale={scale}, max_len={max_len}\n→ {e}"
                )

        self.logger.debug(
            f"[prepare_oracle_df] Completed in {time.time() - start_time:.4f}s"
        )

        return df_imp

    # ------------------------------------------------------
    # Incremental load – remove duplicate keys
    # ------------------------------------------------------

    def remove_duplicates(self, df_imp: pd.DataFrame, df_target: pd.DataFrame, use_unique=True):
        """
        Loại bỏ bản ghi trùng key (incremental)
        """
        start = time.time()

        df_imp.columns = df_imp.columns.str.upper()
        df_target.columns = df_target.columns.str.upper()

        key_cols = [k.upper() for k in self._key_columns]

        # Validate existence
        missing = [c for c in key_cols if c not in df_imp.columns or c not in df_target.columns]
        if missing:
            raise KeyError(f"Missing key columns: {missing}")

        # Convert key columns to string
        for c in key_cols:
            df_imp[c] = df_imp[c].astype(str)
            df_target[c] = df_target[c].astype(str)

        # Build tuple keys
        df_imp["_key_tuple"] = list(zip(*[df_imp[col] for col in key_cols]))
        df_target["_key_tuple"] = list(zip(*[df_target[col] for col in key_cols]))

        if use_unique:
            existing = set(df_target["_key_tuple"].unique())
        else:
            existing = set(df_target["_key_tuple"].values)

        mask = ~df_imp["_key_tuple"].isin(existing)
        df_new = df_imp[mask].copy()
        df_new.drop(columns=["_key_tuple"], inplace=True)

        self.logger.debug(
            f"[remove_duplicates] Kept {df_new.shape[0]} rows in {time.time() - start:.4f}s"
        )
        return df_new.reset_index(drop=True)

    # ------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------

    def normalize_column(self, col):
        return col.apply(lambda x: str(x) if isinstance(x, Decimal) else x)

    def check_max_value(self, v, max_value, min_value=None):
        try:
            if isinstance(v, str):
                v = float(v)
            if v > max_value:
                return max_value
            if min_value is not None and v < min_value:
                return min_value
            return v
        except Exception:
            return v

    def convert_dtype(self, col, db_type):
        mapping = {
            "NUMBER": "float64",
            "VARCHAR2": "str",
            "DATE": "datetime64",
            "BOOLEAN": "bool",
        }
        dtype = mapping.get(db_type, "object")
        return col.astype(dtype, errors="ignore")

    # ------------------------------------------------------
    # BOOLEAN / NUMBER / VARCHAR converters
    # ------------------------------------------------------

    def convert_bool_to_value(self, col, data_type):
        conv = {
            "1": 1, "0": 0,
            "yes": 1, "no": 0,
            "true": 1, "false": 0,
        }
        tmp = col.astype(str).str.lower().replace(conv).fillna(0)

        if data_type == "NUMBER":
            return tmp.astype(int, errors="ignore")

        return tmp.astype(str)

    def convert_number_dtype(self, df_column: pd.Series, precision: int, scale: int) -> pd.Series:
        """
        Rule:
        - Nếu scale > 0 → truncate (KHÔNG round)
        - Nếu scale = 0 → convert int
        - Không clamp
        """
        df_column = df_column.fillna(0)

        if scale > 0:
            # truncate without rounding
            factor = 10 ** scale
            df_column = (df_column.astype(float) * factor).astype(int) / factor
            return df_column

        # scale = 0
        df_column = df_column.astype(float)
        df_column = df_column.astype(int, errors="ignore")
        return df_column

    def convert_number_to_str(self, df_column: pd.Series, max_length: int = None) -> pd.Series:
        df_column = df_column.fillna('')

        def convert_value(x):
            if isinstance(x, float) and x.is_integer():
                return str(int(x))
            elif isinstance(x, str) and x.endswith('.0'):
                return x[:-2]
            return str(x)

        df_column = df_column.apply(convert_value)

        if max_length:
            df_column = df_column.str.slice(0, max_length)

        return df_column

    def convert_str_to_number(self, col, precision, scale):
        def convert(val):
            if val is None:
                return 0
            if re.fullmatch(r"\d+(\.\d+)?", str(val)):
                return float(val) if "." in str(val) else int(val)
            return 0

        return self.convert_number_dtype(col.apply(convert), precision, scale)

    # ------------------------------------------------------
    # DATE converter
    # ------------------------------------------------------

    def convert_to_datetime(self, col: pd.Series) -> pd.Series:

        def detect_fmt(v):
            fmt_map = {
                8: "%Y%m%d",
                6: "%y%m%d",
                12: "%Y%m%d%H%M",
                14: "%Y%m%d%H%M%S"
            }
            return fmt_map.get(len(str(int(v))), None)

        def excel_serial(v):
            base = pd.Timestamp("1899-12-30")
            return base + pd.to_timedelta(v, unit="D")

        def regex_parse(v):
            regex_map = [
                (r"\d{4}/\d{2}/\d{2}", "%Y/%m/%d"),
                (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
                (r"\d{4}\d{2}\d{2}", "%Y%m%d")
            ]
            for pattern, fmt in regex_map:
                if re.match(pattern, v):
                    return pd.to_datetime(v, format=fmt, errors="coerce")
            return pd.NaT

        def convert(v):
            if pd.isna(v):
                return pd.NaT
            if isinstance(v, str):
                v = v.strip()
                # brute-force patterns
                fmts = [
                    "%Y/%m/%d %H:%M:%S",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y%m%d",
                    "%Y%m%d%H%M%S"
                ]
                for fmt in fmts:
                    try:
                        return pd.to_datetime(v, format=fmt)
                    except Exception:
                        pass
                return regex_parse(v)
            if isinstance(v, int):
                fmt = detect_fmt(v)
                if fmt:
                    return pd.to_datetime(str(v), format=fmt)
                return pd.to_datetime(v, errors="coerce")
            if isinstance(v, float) and v > 59:
                return excel_serial(v)
            return pd.NaT

        return col.apply(convert)

    # ------------------------------------------------------
    # HEADER mapping
    # ------------------------------------------------------

    def map_config_header(self, input_header, config_header):
        input_header = [h.strip().upper() for h in input_header]

        if not config_header:
            return input_header.copy()

        cfg = {k.strip().upper(): v.strip().upper()
               for k, v in config_header.items()}

        mapped = [cfg.get(h, h) for h in input_header]
        return mapped

    def df_replace_header(self, df):
        orig = df.columns.tolist()

        cfg_headers = self.template.header or orig
        mapping = self.template.column_mapping

        if mapping:
            cfg_headers = self.map_config_header(cfg_headers, mapping)

        cfg_headers = [x.upper() for x in cfg_headers]

        new_headers = []
        for i, c in enumerate(orig):
            if i < len(cfg_headers):
                new_headers.append(cfg_headers[i])
            else:
                new_headers.append(c.upper())

        df.columns = new_headers
        self.logger.debug(f"[df_replace_header] headers={new_headers}")

        return df

    # ------------------------------------------------------
    # Utils
    # ------------------------------------------------------

    def remove_vietnamese_accents(self, text):
        if not isinstance(text, str):
            return text
        text = unicodedata.normalize("NFD", text)
        text = "".join(c for c in text if unicodedata.category(c) != "Mn")
        return text.replace("Đ", "D").replace("đ", "d")

    def replace_none_with_null(self, v):
        return "<NULL>" if pd.isna(v) else v

    # ------------------------------------------------------
    # SQL builders
    # ------------------------------------------------------

    def convert_sql(self, df):
        cols = ", ".join(df.columns)
        vals = ", ".join([f":{c}" for c in df.columns])
        return f"INSERT /*+ APPEND */ INTO {self.template.table_name} ({cols}) VALUES ({vals})"

    def target_key_sql(self):
        if not self._is_incremental or not self.template.etl.key_columns:
            return None

        if isinstance(self.template.etl.key_columns, list):
            key_cols = ", ".join(self.template.etl.key_columns)
        else:
            key_cols = self.template.etl.key_columns

        sql = f"SELECT {key_cols} FROM {self.template.etl.target_table}"

        if self.template.etl.where_condition:
            sql += " " + self.template.etl.where_condition

        return sql

    def testSql(self, df):
        sql = ""
        base = f"INSERT INTO {self.template.table_name}"

        for _, row in df.iterrows():
            columns = ", ".join(df.columns)
            values = "', '".join(map(str, row.values))
            sql += f"{base} ({columns}) VALUES ('{values}');"

        return sql