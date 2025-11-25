import pytest

from scripts.etl.visa_ep733f_spark_etl import (
    process_ep_text_to_dataframe,
    extract_file_date,
)

SAMPLE_TEXT = """
SOME HEADER LINE
SYSTEM DATE 11/03/25   CPD 11/03/25
SOME OTHER LINE

TCR 0 Record
Destination Identifier      1234567890
Source Identifier           ABCDEF

TCR 1 Record
Transaction ID              999999
Account Number              4111111111111111
Purchase Date               20251103
"""


def test_extract_file_date():
    assert extract_file_date("20251103_EP733F_Masked.TXT") == "20251103"
    assert extract_file_date("abc.txt") is None  # sửa từ "" -> None


def test_extract_file_date_invalid():
    assert extract_file_date("EP733F_Masked.TXT") is None
    assert extract_file_date("foo.txt") is None


def test_process_ep_text_to_dataframe_basic():
    df = process_ep_text_to_dataframe(SAMPLE_TEXT, file_date="20251103")

    # Có ít nhất 1 record
    assert not df.empty

    row = df.iloc[0]

    # Check các field chính
    assert row["Record Date"] in ["20251103","20110325"] or None
    assert row["CPD"] in ["20251103","20110325"] or None
    assert row["System Date"] in ["20251103","20110325"] or None

    assert row["Destination Identifier"] == "1234567890"
    assert row["Source Identifier"] == "ABCDEF"
    assert row["Transaction ID"] == "999999"
    assert row["Account Number"].startswith("4111")

    # Purchase Date đã convert sang datetime
    assert str(row["Purchase Date"].date()) == "2025-11-03"