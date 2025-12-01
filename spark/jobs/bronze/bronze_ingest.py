#!/usr/bin/env python3
# spark/jobs/bronze/bronze_ingest.py
"""
Ingest CSV -> Bronze Parquet (add metadata).
Supports dataset parameter: customers | transactions
"""
# import sys
# if "/opt/spark/jobs" not in sys.path:
#     sys.path.insert(0, "/opt/spark/jobs")
import argparse
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import input_file_name, current_timestamp
from common.s3_config import init_s3a
from common.schemas import CUSTOMERS_SCHEMA, TRANSACTIONS_SCHEMA

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bronze_ingest")

SCHEMAS = {
    "customers": CUSTOMERS_SCHEMA,
    "transactions": TRANSACTIONS_SCHEMA,
}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--minio-endpoint", required=True)
    p.add_argument("--minio-access-key", required=True)
    p.add_argument("--minio-secret-key", required=True)
    p.add_argument("--bronze-bucket", required=True)
    p.add_argument("--dataset", required=True, choices=["customers", "transactions"])
    p.add_argument("--input-path", default=None, help="Optional: override src file path inside bucket")
    p.add_argument("--out-prefix", default="parquet")
    args = p.parse_args()

    spark = SparkSession.builder.appName(f"bronze_ingest_{args.dataset}").getOrCreate()
    init_s3a(spark, args.minio_endpoint, args.minio_access_key, args.minio_secret_key)

    schema = SCHEMAS[args.dataset]
    src = args.input_path or f"s3a://{args.bronze_bucket}/{args.dataset}/{args.dataset}.csv"
    dest = f"s3a://{args.bronze_bucket}/{args.out_prefix}/{args.dataset}/"

    log.info("Reading source: %s", src)
    df = (spark.read
          .option("header", True)
          .option("mode", "FAILFAST")
          .schema(schema)
          .csv(src)
          .withColumn("_ingest_ts", current_timestamp())
          .withColumn("_source_file", input_file_name())
         )
    log.info("Schema read:")
    df.printSchema()

    # write parquet with partition hint (for transactions we may partition by value_date year/month)
    if args.dataset == "transactions":
        # Partition by year/month for better query performance (assumes value_date not null)
        df = df.withColumn("_value_year", df["value_date"].cast("date").substr(1,4))
        df.write.mode("overwrite").partitionBy("_value_year").parquet(dest)
    else:
        df.write.mode("overwrite").parquet(dest)

    log.info("Wrote bronze parquet to %s", dest)
    spark.stop()

if __name__ == "__main__":
    main()