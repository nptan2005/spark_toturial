from __future__ import annotations
import os
import logging
from datetime import timedelta
from urllib.parse import urlparse

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.exceptions import AirflowFailException
from airflow.models import Connection
from airflow import settings

log = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "tan",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

# session = settings.Session()

# conn = Connection(
#     conn_id="local_spark",
#     conn_type="spark",
#     host="spark-master",
#     port=7077,
#     extra={
#         "spark_home": "/opt/spark",
#         "spark_submit_bin": "/opt/spark/bin/spark-submit"
#     }
# )

# session.merge(conn)
# session.commit()

# --- MINIO / BUCKETS
# MINIO_ENDPOINT may be either "minio:9000" (recommended for Minio client)
# or "http://minio:9000" (if passed). We normalize when creating minio client.
MINIO_ENDPOINT_RAW = os.getenv("MINIO_ENDPOINT", "minio:9000")           # for Minio client (host:port or URL)
MINIO_S3A_ENDPOINT = os.getenv("MINIO_S3A_ENDPOINT", "http://minio:9000")  # for spark s3a (must include scheme)
MINIO_BUCKET_BRONZE = os.getenv("MINIO_BRONZE_BUCKET", "bronze")
MINIO_BUCKET_SILVER = os.getenv("MINIO_SILVER_BUCKET", "silver")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "admin123")

# --- GCP / BQ
GCS_BUCKET = os.getenv("GCS_BUCKET", "my-cdp-demo-gcs")
GCP_CONN_ID = os.getenv("GCP_CONN_ID", "google_cloud_default")
PROJECT_ID = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT") or "my-cdp-demo-01"

# --- SPARK / PATHS (from ENV)
SPARK_MASTER = os.getenv("SPARK_MASTER", os.getenv("SPARK_MASTER_HOST", "spark-master"))
if not SPARK_MASTER.startswith("spark://"):
    sp_host = os.getenv("SPARK_MASTER_HOST", "spark-master")
    sp_port = os.getenv("SPARK_MASTER_PORT", "7077")
    SPARK_MASTER = f"spark://{sp_host}:{sp_port}"

SPARK_HOME = os.getenv("SPARK_HOME", "/opt/spark")
SPARK_SUBMIT_BIN = os.getenv("SPARK_SUBMIT_BIN", "/opt/spark/bin/spark-submit")
SPARK_JARS = os.getenv("SPARK_JARS", "/opt/spark/jars/hadoop-aws-3.3.4.jar,/opt/spark/jars/aws-java-sdk-bundle-1.12.548.jar")

# python path inside airflow container (where spark-submit runs) and on workers
PYSPARK_DRIVER_PYTHON = os.getenv("PYSPARK_DRIVER_PYTHON", "/usr/bin/python3")
PYSPARK_PYTHON = os.getenv("PYSPARK_PYTHON", "/usr/bin/python3")

# jars
HADOOP_AWS_JAR = os.getenv("HADOOP_AWS_JAR", "/opt/spark/jars/hadoop-aws-3.3.4.jar")
AWS_SDK_JAR = os.getenv("AWS_SDK_JAR", "/opt/spark/jars/aws-java-sdk-bundle-1.12.548.jar")

DATA_PREFIX_BRONZE = "customers"
DATA_PREFIX_TX = "transactions"

with DAG(
    dag_id="cdp_demo_pipeline",
    start_date=days_ago(1),
    schedule_interval=None,
    default_args=DEFAULT_ARGS,
    catchup=False,
    max_active_runs=1,
    tags=["cdp", "demo"],
) as dag:

    def upload_demo_to_minio():
        from minio import Minio
        import pathlib

        
        # KHỞI TẠO CLIENT BẰNG CHUỖI HOST:PORT ĐÃ CHUẨN HÓA
        client = Minio(
            MINIO_ENDPOINT_RAW, 
            access_key=MINIO_ROOT_USER, 
            secret_key=MINIO_ROOT_PASSWORD, 
            secure=False
        )

        for b in (MINIO_BUCKET_BRONZE, MINIO_BUCKET_SILVER):
            if not client.bucket_exists(b):
                client.make_bucket(b)
                log.info("Created bucket %s", b)

        base = pathlib.Path("/data/demo")
        files = {
            f"{DATA_PREFIX_BRONZE}/customers.csv": base / "customers.csv",
            f"{DATA_PREFIX_TX}/transactions.csv": base / "transactions.csv",
        }
        for key, local in files.items():
            if not local.exists():
                raise AirflowFailException(f"Demo file missing: {local}")
            client.fput_object(MINIO_BUCKET_BRONZE, key, str(local))
            log.info("Uploaded %s -> s3a://%s/%s", local, MINIO_BUCKET_BRONZE, key)

    t_upload_to_minio = PythonOperator(
        task_id="upload_to_minio",
        python_callable=upload_demo_to_minio,
        retries=0,
    )

    # common conf built from ENV (DAG-driven)
    common_conf = {
        # ensure Spark master is a valid URL
        "spark.master": SPARK_MASTER,
        # s3a / minio (spark needs http://)
        "spark.hadoop.fs.s3a.endpoint": os.getenv("MINIO_S3A_ENDPOINT", MINIO_S3A_ENDPOINT),
        "spark.hadoop.fs.s3a.access.key": MINIO_ROOT_USER,
        "spark.hadoop.fs.s3a.secret.key": MINIO_ROOT_PASSWORD,
        "spark.hadoop.fs.s3a.path.style.access": "true",
        "spark.hadoop.fs.s3a.connection.ssl.enabled": "false",
        "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem",
        "spark.hadoop.fs.s3a.aws.credentials.provider": "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
        # pyspark python locations (driver = where spark-submit runs)
        "spark.pyspark.driver.python": PYSPARK_DRIVER_PYTHON,
        "spark.pyspark.python": PYSPARK_PYTHON,
        # jars
        "spark.jars": SPARK_JARS,
        # optional deploy mode
        "spark.submit.deployMode": os.getenv("SPARK_DEPLOY_MODE", "client"),
    }

    t_bronze_to_parquet = SparkSubmitOperator(
        task_id="bronze_to_parquet",
        application="/opt/spark/jobs/bronze_to_parquet.py",
        conn_id="local_spark",
        verbose=True,
        application_args=[
            "--minio-endpoint", os.getenv("MINIO_S3A_ENDPOINT", MINIO_S3A_ENDPOINT),
            "--minio-access-key", MINIO_ROOT_USER,
            "--minio-secret-key", MINIO_ROOT_PASSWORD,
            "--bronze-bucket", MINIO_BUCKET_BRONZE,
            "--out-prefix", "parquet"
        ],
        conf=common_conf,
    )

    t_silver_transform = SparkSubmitOperator(
        task_id="bronze_to_silver",
        application="/opt/spark/jobs/bronze_to_silver.py",
        conn_id="local_spark",
        verbose=True,
        application_args=[
            "--minio-endpoint", os.getenv("MINIO_S3A_ENDPOINT", MINIO_S3A_ENDPOINT),
            "--minio-access-key", MINIO_ROOT_USER,
            "--minio-secret-key", MINIO_ROOT_PASSWORD,
            "--bronze-bucket", MINIO_BUCKET_BRONZE,
            "--silver-bucket", MINIO_BUCKET_SILVER,
            "--bronze-prefix", "parquet",
            "--silver-prefix", "parquet"
        ],
        conf=common_conf,
    )

    def push_silver_to_gcs(**context):
        from minio import Minio
        import tempfile, shutil, pathlib
        from airflow.providers.google.cloud.hooks.gcs import GCSHook

        # KHỞI TẠO CLIENT BẰNG CHUỖI HOST:PORT ĐÃ CHUẨN HÓA
        client = Minio(
            MINIO_ENDPOINT_RAW, 
            access_key=MINIO_ROOT_USER, 
            secret_key=MINIO_ROOT_PASSWORD, 
            secure=False
        )

        tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="silver_"))
        try:
            prefix = "parquet"
            for obj in client.list_objects(MINIO_BUCKET_SILVER, prefix=prefix, recursive=True):
                dest = tmpdir / obj.object_name[len(prefix)+1 :] if obj.object_name.startswith(prefix + "/") else tmpdir / obj.object_name
                dest.parent.mkdir(parents=True, exist_ok=True)
                client.fget_object(MINIO_BUCKET_SILVER, obj.object_name, str(dest))
                log.info("Downloaded %s -> %s", obj.object_name, dest)

            gcs = GCSHook(gcp_conn_id=GCP_CONN_ID)
            bucket_name = GCS_BUCKET
            files = list(tmpdir.glob("**/*"))
            uploaded = 0
            for f in files:
                if f.is_file():
                    remote_path = os.path.join("silver", "parquet", f.relative_to(tmpdir).as_posix())
                    gcs.upload(bucket_name, remote_path, str(f))
                    uploaded += 1
                    log.info("Uploaded %s -> gs://%s/%s", f, bucket_name, remote_path)
            if uploaded == 0:
                raise AirflowFailException("No files uploaded to GCS (empty silver)")
        finally:
            shutil.rmtree(tmpdir)

    t_push_gcs = PythonOperator(task_id="push_silver_to_gcs", python_callable=push_silver_to_gcs)

    t_load_bq = BigQueryInsertJobOperator(
        task_id="load_silver_to_bq",
        gcp_conn_id=GCP_CONN_ID,
        configuration={
            "load": {
                "sourceUris": [f"gs://{GCS_BUCKET}/silver/parquet/*.parquet"],
                "destinationTable": {"projectId": PROJECT_ID, "datasetId": "cdp_demo", "tableId": "transactions"},
                "sourceFormat": "PARQUET",
                "writeDisposition": "WRITE_TRUNCATE",
                "autodetect": True,
            }
        },
        location="US",
    )

    t_upload_to_minio >> t_bronze_to_parquet >> t_silver_transform >> t_push_gcs >> t_load_bq