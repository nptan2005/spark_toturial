from pathlib import Path

import pytest

from scripts.etl.visa_ep733f_spark_etl import (
    process_ep_text_to_dataframe,
    extract_file_date,
)


def test_process_real_file_if_exists():
    # tests/ -> airflow_home/ -> data/visa_ep/...
    root = Path(__file__).resolve().parents[1]
    sample_path = root / "data" / "visa_ep" / "20251103_EP733F_Masked.TXT"

    if not sample_path.exists():
        pytest.skip(f"Sample file not found: {sample_path}")

    content = sample_path.read_text(encoding="utf-8", errors="ignore")
    file_date = extract_file_date(sample_path.name)

    df = process_ep_text_to_dataframe(content, file_date)

    assert not df.empty
    # Tùy em, có thể thêm các assert khác: cột tồn tại, số dòng > X, v.v.
    for col in ["Record Date", "Transaction ID", "Account Number"]:
        assert col in df.columns