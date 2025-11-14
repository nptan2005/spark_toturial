# oracle_to_parquet.py
from pyspark.sql import SparkSession
import os

spark = SparkSession.builder \
    .appName("oracle_to_parquet") \
    .getOrCreate()

# Oracle JDBC settings
oracle_host = os.getenv("ORACLE_HOST", "oradb")
oracle_port = os.getenv("ORACLE_PORT", "1521")
oracle_service = os.getenv("ORACLE_SERVICE", "ORCLCDB")  # tùy image
oracle_url = f"jdbc:oracle:thin:@//{oracle_host}:{oracle_port}/{oracle_service}"
oracle_user = os.getenv("ORACLE_USER", "system")
oracle_pass = os.getenv("ORACLE_PASS", "Oracle123")

table = os.getenv("ORACLE_TABLE", "SOURCE_TRANSACTIONS")

df = spark.read.format("jdbc")\
    .option("url", oracle_url)\
    .option("dbtable", table)\
    .option("user", oracle_user)\
    .option("password", oracle_pass)\
    .option("driver", "oracle.jdbc.OracleDriver")\
    .load()

out_path = os.getenv("OUT_PATH", "/data/staging/transactions")
df.write.mode("overwrite").parquet(out_path)

spark.stop()