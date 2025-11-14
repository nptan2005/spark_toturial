# parquet_to_postgres.py
from pyspark.sql import SparkSession
import os

spark = SparkSession.builder.appName("parquet_to_postgres").getOrCreate()

in_path = os.getenv("IN_PATH", "/data/staging/transactions")
df = spark.read.parquet(in_path)

# simple transform example
df_clean = df.selectExpr("tx_id", "account_no", "amount", "tx_time")

pg_url = os.getenv("PG_URL", "jdbc:postgresql://postgres-dwh:5432/dwhdb")
pg_props = {
    "user": os.getenv("PG_USER", "dwh"),
    "password": os.getenv("PG_PASS", "dwh123"),
    "driver": "org.postgresql.Driver"
}

# write to ods.transactions
df_clean.write.jdbc(url=pg_url, table="ods.transactions", mode="append", properties=pg_props)

spark.stop()