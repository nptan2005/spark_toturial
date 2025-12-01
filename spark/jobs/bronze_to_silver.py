#!/usr/bin/env python3
import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

parser = argparse.ArgumentParser()
parser.add_argument("--minio-endpoint", required=True)
parser.add_argument("--minio-access-key", required=True)
parser.add_argument("--minio-secret-key", required=True)
parser.add_argument("--bronze-bucket", required=True)
parser.add_argument("--silver-bucket", required=True)
parser.add_argument("--bronze-prefix", default="parquet")
parser.add_argument("--silver-prefix", default="parquet")
args = parser.parse_args()

spark = SparkSession.builder.appName("bronze-to-silver").getOrCreate()

# config s3a
hadoop_conf = spark.sparkContext._jsc.hadoopConfiguration()
hadoop_conf.set("fs.s3a.endpoint", args.minio_endpoint)
hadoop_conf.set("fs.s3a.access.key", args.minio_access_key)
hadoop_conf.set("fs.s3a.secret.key", args.minio_secret_key)
hadoop_conf.set("fs.s3a.path.style.access", "true")
hadoop_conf.set("fs.s3a.connection.ssl.enabled", "false")
hadoop_conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
hadoop_conf.set("fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")

bronze_parquet = f"s3a://{args.bronze_bucket}/{args.bronze_prefix}/transactions/"
silver_parquet = f"s3a://{args.silver_bucket}/{args.silver_prefix}/transactions/"

print("READING:", bronze_parquet)

df = spark.read.parquet(bronze_parquet)

print("SCHEMA READ FROM PARQUET:")
df.printSchema()

# bắt buộc có transaction_id
if "transaction_id" not in df.columns:
    raise Exception(f"Missing transaction_id column! Columns = {df.columns}")

# Clean + dedupe
if "timestamp" in df.columns:
    df = df.orderBy(col("timestamp").desc()).dropDuplicates(["transaction_id"])
else:
    df = df.dropDuplicates(["transaction_id"])

print("WRITING SILVER TO:", silver_parquet)
df.write.mode("overwrite").parquet(silver_parquet)

spark.stop()