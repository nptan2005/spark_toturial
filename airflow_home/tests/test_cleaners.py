import pytest
from scripts.etl.visa_ep733f_spark_etl import (
    clean_line, normalize_label, map_label_to_header,
    extract_file_date
)

def test_clean_line_removes_control_chars():
    assert clean_line("Hello\x00World") == "HelloWorld"
    assert clean_line("A\x7FB") == "AB"

def test_normalize_label():
    assert normalize_label("Transaction   ID") == "transaction id"
    assert normalize_label("Account-Number") == "account number"

def test_map_label_to_header_basic():
    assert map_label_to_header("Transaction ID") == "Transaction ID"
    assert map_label_to_header("terminal id") == "Terminal ID"

def test_map_label_to_header_fuzzy():
    assert map_label_to_header("TCQ") == "TCQ of financial tran"
    assert map_label_to_header("Account Num") == "Account Number"

def test_extract_file_date():
    assert extract_file_date("20251103_EP733F_Masked.TXT") == "20251103"
    assert extract_file_date("abc.txt") == ""