import pytest
import pandas as pd
from scripts.etl.visa_ep733f_spark_etl import (
    process_ep_text_to_dataframe
)

def test_process_dataframe_basic():
    content = """
SYSTEM DATE 24/11/03   ...   CPD 24/11/03
TCR 0 Record
Destination Identifier     ABC
Source Identifier          DEF
Transaction ID             12345
"""

    df = process_ep_text_to_dataframe(content, "20251103")
    assert not df.empty
    assert "Transaction ID" in df.columns
    assert df.loc[0, "Record Date"] == "20251103"
    assert df.loc[0, "Destination Identifier"] == "ABC"
    assert df.loc[0, "Source Identifier"] == "DEF"

def test_numeric_conversions():
    content = """
TCR 0 Record
Source Amount              +000012345
Settlement amount - Inter  -000000678
Interchange Fee Amount     000000123
"""

    df = process_ep_text_to_dataframe(content, "20250101")
    assert float(df.loc[0, "Source Amount"]) == 12345
    assert float(df.loc[0, "Settlement amount - Inter"]) == -678
    assert float(df.loc[0, "Interchange Fee Amount"]) == 123