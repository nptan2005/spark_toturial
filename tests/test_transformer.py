import pandas as pd
import pytest

from common_lib.transform.data_transformer import DataTransformer
from common_lib.importer.models import import_configuration


def test_df_replace_header():
    df = pd.DataFrame({"A": [1], "B": [2]})

    transformer = DataTransformer("ACQ_BANK_BENEFIT")

    df2 = transformer.df_replace_header(df)

    # expected header
    assert df2.columns[0] == "BANK_NAME"
    assert df2.columns[1] == "ACQ_BANK_CODE"


def test_convert_number_dtype():
    transformer = DataTransformer("ACQ_BANK_BENEFIT")

    df = pd.Series([1.234, 9999.99, None])
    rs = transformer.convert_number_dtype(df, precision=5, scale=2)

    assert rs.iloc[0] == 1.23
    assert rs.iloc[1] == 9999.99
    assert rs.iloc[2] == 0  # filled NaN


def test_remove_duplicates():
    transformer = DataTransformer("ACQ_BANK_BENEFIT")
    transformer._key_columns = ["BANK_NAME"]

    df_imp = pd.DataFrame({"BANK_NAME": ["A", "B", "C"]})
    df_target = pd.DataFrame({"BANK_NAME": ["B"]})

    df_filtered = transformer.remove_duplicates(df_imp, df_target)

    assert df_filtered.shape[0] == 2
    assert "B" not in df_filtered["BANK_NAME"].values