# spark/jobs/common/schemas.py
"""
Định nghĩa schema cố định cho dataset để tránh inferSchema (production best practice).
"""
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DoubleType, DateType, TimestampType

CUSTOMERS_SCHEMA = StructType([
    StructField("customer_id", IntegerType(), True),
    StructField("customer_code", StringType(), True),
    StructField("full_name", StringType(), True),
    StructField("dob", DateType(), True),
    StructField("gender", StringType(), True),
    StructField("national_id", StringType(), True),
    StructField("segment", StringType(), True),
    StructField("target_code", StringType(), True),
    StructField("sector_code", StringType(), True),
    StructField("industry_code", StringType(), True),
])

TRANSACTIONS_SCHEMA = StructType([
    StructField("txn_id", StringType(), True),
    StructField("customer_id", IntegerType(), True),
    StructField("product_code", StringType(), True),
    StructField("branch_code", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("currency", StringType(), True),
    StructField("value_date", DateType(), True),
    StructField("maturity_date", DateType(), True),
    StructField("interest_rate", DoubleType(), True),
    StructField("txn_type", StringType(), True),
    StructField("create_date", TimestampType(), True),
])