#!/usr/bin/env python3
# spark/jobs/silver/transform_silver.py
"""
Clean + standardize bronze -> silver.
Ví dụ rules:
 - normalise column names to snake_case
 - enforce non-null business keys
 - cast types (đã dùng schema ở bronze, nhưng vẫn check)
 - data quality checks (simple)
 - dedupe by business key
"""
# import sys
# if "/opt/spark/jobs" not in sys.path:
#     sys.path.insert(0, "/opt/spark/jobs")
import argparse
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import trim, lower, col
from common.s3_config import init_s3a

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("transform_silver")

def clean_customers(df):
    df2 = (df
           .withColumn("customer_code", trim(col("customer_code")))
           .withColumn("full_name", trim(col("full_name")))
           .withColumn("national_id", trim(col("national_id")))
           .withColumn("gender", trim(col("gender")))
          )
    # business checks
    df2 = df2.filter(col("customer_id").isNotNull())
    df2 = df2.dropDuplicates(["customer_id"])
    return df2

def clean_transactions(df):
    df2 = (df
           .withColumn("txn_id", trim(col("txn_id")))
           .withColumn("product_code", trim(col("product_code")))
           .withColumn("branch_code", trim(col("branch_code")))
          )
    # enforce business rules
    df2 = df2.filter(col("txn_id").isNotNull())
    df2 = df2.filter(col("amount").isNotNull())
    df2 = df2.filter(col("amount") >= 0)
    df2 = df2.dropDuplicates(["txn_id"])
    return df2

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--minio-endpoint", required=True)
    p.add_argument("--minio-access-key", required=True)
    p.add_argument("--minio-secret-key", required=True)
    p.add_argument("--bronze-bucket", required=True)
    p.add_argument("--silver-bucket", required=True)
    p.add_argument("--dataset", required=True, choices=["customers","transactions"])
    p.add_argument("--bronze-prefix", default="parquet")
    p.add_argument("--silver-prefix", default="parquet")
    args = p.parse_args()

    spark = SparkSession.builder.appName(f"silver_transform_{args.dataset}").getOrCreate()
    init_s3a(spark, args.minio_endpoint, args.minio_access_key, args.minio_secret_key)

    bronze_path = f"s3a://{args.bronze_bucket}/{args.bronze_prefix}/{args.dataset}/"
    silver_path = f"s3a://{args.silver_bucket}/{args.silver_prefix}/{args.dataset}/"

    log.info("Reading bronze from %s", bronze_path)
    df = spark.read.parquet(bronze_path)
    log.info("Bronze schema:")
    df.printSchema()

    if args.dataset == "customers":
        df_clean = clean_customers(df)
    else:
        df_clean = clean_transactions(df)

    # additional QC: count rows
    cnt = df_clean.count()
    log.info("After cleaning, %d rows", cnt)

    # write silver (partitioning for transactions recommended)
    if args.dataset == "transactions":
        df_clean.write.mode("overwrite").parquet(silver_path)
    else:
        df_clean.write.mode("overwrite").parquet(silver_path)

    log.info("Wrote silver to %s", silver_path)
    spark.stop()

if __name__ == "__main__":
    main()