#!/usr/bin/env python3
import argparse
from pyspark.sql import SparkSession

parser = argparse.ArgumentParser()
parser.add_argument("--minio-endpoint", required=True)
parser.add_argument("--minio-access-key", required=True)
parser.add_argument("--minio-secret-key", required=True)
parser.add_argument("--bronze-bucket", required=True)
parser.add_argument("--out-prefix", default="parquet")
args = parser.parse_args()

spark = SparkSession.builder.appName("bronze-to-parquet").getOrCreate()

# config s3a
hadoop_conf = spark.sparkContext._jsc.hadoopConfiguration()
hadoop_conf.set("fs.s3a.endpoint", args.minio_endpoint)
hadoop_conf.set("fs.s3a.access.key", args.minio_access_key)
hadoop_conf.set("fs.s3a.secret.key", args.minio_secret_key)
hadoop_conf.set("fs.s3a.path.style.access", "true")
hadoop_conf.set("fs.s3a.connection.ssl.enabled", "false")
hadoop_conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
hadoop_conf.set("fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")

# chính xác file CSV
csv_path = f"s3a://{args.bronze_bucket}/transactions/transactions.csv"

df = spark.read.csv(
    csv_path,
    header=True,
    inferSchema=True,
    sep=",",
)

print("CSV SCHEMA:")
df.printSchema()

out_path = f"s3a://{args.bronze_bucket}/{args.out_prefix}/transactions/"
print("WRITING PARQUET TO:", out_path)

df.write.mode("overwrite").parquet(out_path)

spark.stop()