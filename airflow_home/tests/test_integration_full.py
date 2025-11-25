import pytest
from scripts.etl.visa_ep733f_spark_etl import (
    process_ep_text_to_dataframe, extract_file_date
)

def test_integration_parse_full_sample(spark):
    # Load sample text
    sample_path = "../data/visa_ep/20251103_EP733F_Masked.TXT"
    with open(sample_path, "r", encoding="utf-8") as f:
        content = f.read()

    file_date = extract_file_date("20251103_EP733F_Masked.TXT")
    df = process_ep_text_to_dataframe(content, file_date)

    assert df.shape[0] > 0
    assert "Transaction ID" in df.columns
    assert df["Record Date"].iloc[0] == "20251103"

    # spark conversion
    from pyspark.sql.types import StructType, StructField, StringType

    schema = StructType([StructField(c, StringType(), True) for c in df.columns])
    sdf = spark.createDataFrame(df.astype(str), schema=schema)

    assert sdf.count() == df.shape[0]
    assert set(sdf.columns) == set(df.columns)