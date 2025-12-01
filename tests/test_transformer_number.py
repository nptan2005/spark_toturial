import pandas as pd
from common_lib.transform.data_transformer import DataTransformer

def test_convert_number_dtype_scale():
    transformer = DataTransformer("ACQ_BANK_BENEFIT")

    df = pd.Series([1.234, 9999.999, None])
    rs = transformer.convert_number_dtype(df, precision=10, scale=2)

    assert rs.iloc[0] == 1.23
    assert rs.iloc[1] == 9999.99
    assert rs.iloc[2] == 0


def test_convert_number_dtype_no_scale():
    transformer = DataTransformer("ACQ_BANK_BENEFIT")

    df = pd.Series([1.234, 9999.99, None])
    rs = transformer.convert_number_dtype(df, precision=5, scale=0)

    assert rs.iloc[0] == 1
    assert rs.iloc[1] == 9999
    assert rs.iloc[2] == 0


def test_convert_str_to_number():
    transformer = DataTransformer("ACQ_BANK_BENEFIT")

    df = pd.Series(["123", "456.78", "abc", None])
    rs = transformer.convert_str_to_number(df, precision=10, scale=2)

    assert rs.iloc[0] == 123
    assert rs.iloc[1] == 456.78
    assert rs.iloc[2] == 0
    assert rs.iloc[3] == 0


def test_convert_number_to_str():
    transformer = DataTransformer("ACQ_BANK_BENEFIT")

    df = pd.Series([123, 456.0, 789.10, None])
    rs = transformer.convert_number_to_str(df, max_length=10)

    assert rs.iloc[0] == "123"
    assert rs.iloc[1] == "456"
    assert rs.iloc[2] == "789.1"
    assert rs.iloc[3] == ""