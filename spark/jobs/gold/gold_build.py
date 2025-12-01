#!/usr/bin/env python3
import argparse
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from common.s3_config import init_s3a

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("gold_build")

def build_dim_customer(df_customers):
    return df_customers.select(
        col("customer_id"),
        col("customer_code"),
        col("full_name"),
        col("dob"),
        col("gender"),
        col("segment"),
        col("national_id")
    ).dropDuplicates(["customer_id"])

def build_fact_transactions(df_tx, df_cust):
    df = (df_tx.alias("t")
          .join(df_cust.alias("c"), col("t.customer_id") == col("c.customer_id"), "left")
          .select(
              "t.txn_id", "t.customer_id", "c.customer_code",
              "t.product_code", "t.branch_code", "t.amount",
              "t.currency", "t.value_date", "t.maturity_date",
              "t.interest_rate", "t.txn_type", "t.create_date"
          ))
    return df

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--minio-endpoint", required=True)
    p.add_argument("--minio-access-key", required=True)
    p.add_argument("--minio-secret-key", required=True)
    p.add_argument("--silver-bucket", required=True)
    p.add_argument("--gold-bucket", required=True)
    p.add_argument("--silver-prefix", default="parquet")
    p.add_argument("--gold-prefix", default="parquet")
    args = p.parse_args()

    spark = SparkSession.builder.appName("gold_build").getOrCreate()
    init_s3a(spark, args.minio_endpoint, args.minio_access_key, args.minio_secret_key)

    silver_customers = f"s3a://{args.silver_bucket}/{args.silver_prefix}/customers/"
    silver_transactions = f"s3a://{args.silver_bucket}/{args.silver_prefix}/transactions/"
    gold_dim = f"s3a://{args.gold_bucket}/{args.gold_prefix}/dim_customer/"
    gold_fact = f"s3a://{args.gold_bucket}/{args.gold_prefix}/fact_transactions/"

    log.info("READ CUSTOMERS FROM: %s", silver_customers)
    log.info("READ TRANSACTIONS FROM: %s", silver_transactions)

    df_cust = spark.read.parquet(silver_customers)
    df_tx = spark.read.parquet(silver_transactions)

    dim_customer = build_dim_customer(df_cust)
    fact_tx = build_fact_transactions(df_tx, df_cust)

    dim_customer.write.mode("overwrite").parquet(gold_dim)
    fact_tx.write.mode("overwrite").parquet(gold_fact)

    log.info("WRITE GOLD DIM TO: %s", gold_dim)
    log.info("WRITE GOLD FACT TO: %s", gold_fact)
    spark.stop()

if __name__ == "__main__":
    main()