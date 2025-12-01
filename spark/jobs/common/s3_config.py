# spark/jobs/common/s3_config.py
"""
Helper để init cấu hình S3A / MinIO cho Spark. Reusable.
"""
from pyspark.sql import SparkSession

def init_s3a(spark: SparkSession, endpoint: str, access_key: str, secret_key: str):
    hconf = spark.sparkContext._jsc.hadoopConfiguration()
    # Endpoint có thể là http://minio:9000 hoặc https...
    hconf.set("fs.s3a.endpoint", endpoint)
    hconf.set("fs.s3a.access.key", access_key)
    hconf.set("fs.s3a.secret.key", secret_key)
    hconf.set("fs.s3a.path.style.access", "true")
    # Nếu MinIO không dùng ssl:
    if endpoint.startswith("http://"):
        hconf.set("fs.s3a.connection.ssl.enabled", "false")
    else:
        hconf.set("fs.s3a.connection.ssl.enabled", "true")
    hconf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    hconf.set("fs.s3a.aws.credentials.provider",
              "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")