from __future__ import annotations
import os
import logging
from datetime import timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.utils.dates import days_ago

log = logging.getLogger(__name__)

MINIO_ENDPOINT_RAW = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_S3A_ENDPOINT = os.getenv("MINIO_S3A_ENDPOINT", "http://minio:9000")
MINIO_BUCKET_BRONZE = os.getenv("MINIO_BRONZE_BUCKET", "bronze")
MINIO_BUCKET_SILVER = os.getenv("MINIO_SILVER_BUCKET", "silver")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "admin123")

SPARK_MASTER = "spark://spark-master:7077"
SPARK_BIN = "/opt/spark/bin/spark-submit"

GCS_BUCKET = os.getenv("GCS_BUCKET", "my-cdp-demo-bucket-123")
GCP_CONN_ID = "google_cloud_default"
PROJECT_ID = "my-cdp-demo-01"

DEFAULT_ARGS = {
    "owner": "tan",
    "retries": 0,
}


def upload_demo_to_minio():
    from minio import Minio
    import pathlib

    client = Minio(MINIO_ENDPOINT_RAW,
                   access_key=MINIO_ROOT_USER,
                   secret_key=MINIO_ROOT_PASSWORD,
                   secure=False)

    for b in (MINIO_BUCKET_BRONZE, MINIO_BUCKET_SILVER):
        if not client.bucket_exists(b):
            client.make_bucket(b)

    base = pathlib.Path("/data/demo")
    client.fput_object(MINIO_BUCKET_BRONZE, "customers/customers.csv", base/"customers.csv")
    client.fput_object(MINIO_BUCKET_BRONZE, "transactions/transactions.csv", base/"transactions.csv")


with DAG(
    "cdp_demo_pipeline_simplified",
    default_args=DEFAULT_ARGS,
    start_date=days_ago(1),
    schedule_interval=None,
    catchup=False,
    tags=["cdp", "demo"],
) as dag:

    t_upload = PythonOperator(
        task_id="upload_to_minio",
        python_callable=upload_demo_to_minio,
    )

    # -------------------------------
    # ⭐ Spark step 1: Bronze → Parquet
    # -------------------------------
    t_bronze_to_parquet = BashOperator(
        task_id="bronze_to_parquet",
        bash_command=f"""
        {SPARK_BIN} \
          --master {SPARK_MASTER} \
          --conf spark.hadoop.fs.s3a.endpoint={MINIO_S3A_ENDPOINT} \
          --conf spark.hadoop.fs.s3a.access.key={MINIO_ROOT_USER} \
          --conf spark.hadoop.fs.s3a.secret.key={MINIO_ROOT_PASSWORD} \
          --conf spark.hadoop.fs.s3a.path.style.access=true \
          --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false \
          --jars /opt/spark/jars/hadoop-aws-3.3.4.jar,/opt/spark/jars/aws-java-sdk-bundle-1.12.548.jar \
          /opt/spark/jobs/bronze_to_parquet.py \
          --minio-endpoint {MINIO_S3A_ENDPOINT} \
          --minio-access-key {MINIO_ROOT_USER} \
          --minio-secret-key {MINIO_ROOT_PASSWORD} \
          --bronze-bucket {MINIO_BUCKET_BRONZE} \
          --out-prefix parquet
        """
    )

    # -------------------------------
    # ⭐ Spark step 2: Silver transform
    # -------------------------------
    t_silver = BashOperator(
        task_id="bronze_to_silver",
        bash_command=f"""
        {SPARK_BIN} \
          --master {SPARK_MASTER} \
          --conf spark.hadoop.fs.s3a.endpoint={MINIO_S3A_ENDPOINT} \
          --conf spark.hadoop.fs.s3a.access.key={MINIO_ROOT_USER} \
          --conf spark.hadoop.fs.s3a.secret.key={MINIO_ROOT_PASSWORD} \
          --conf spark.hadoop.fs.s3a.path.style.access=true \
          --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false \
          --jars /opt/spark/jars/hadoop-aws-3.3.4.jar,/opt/spark/jars/aws-java-sdk-bundle-1.12.548.jar \
          /opt/spark/jobs/bronze_to_silver.py \
          --minio-endpoint {MINIO_S3A_ENDPOINT} \
          --minio-access-key {MINIO_ROOT_USER} \
          --minio-secret-key {MINIO_ROOT_PASSWORD} \
          --bronze-bucket {MINIO_BUCKET_BRONZE} \
          --silver-bucket {MINIO_BUCKET_SILVER} \
          --bronze-prefix parquet \
          --silver-prefix parquet
        """
    )

    # -------------------------------
    # Upload to GCS
    # -------------------------------
    def push_silver_to_gcs():
        from minio import Minio
        import os, tempfile, pathlib, shutil
        client = Minio(MINIO_ENDPOINT_RAW,
                       access_key=MINIO_ROOT_USER,
                       secret_key=MINIO_ROOT_PASSWORD,
                       secure=False)

        tmp = pathlib.Path(tempfile.mkdtemp())
        for obj in client.list_objects(MINIO_BUCKET_SILVER, "parquet", recursive=True):
            dest = tmp / obj.object_name
            dest.parent.mkdir(parents=True, exist_ok=True)
            client.fget_object(MINIO_BUCKET_SILVER, obj.object_name, str(dest))

        gcs = GCSHook(gcp_conn_id=GCP_CONN_ID)
        for f in tmp.rglob("*.parquet"):
            gcs.upload(GCS_BUCKET,
                       f"silver/{f.name}",
                       str(f))

        shutil.rmtree(tmp)

    t_push_gcs = PythonOperator(
        task_id="push_silver_to_gcs",
        python_callable=push_silver_to_gcs,
    )

    # -------------------------------
    # Load BQ
    # -------------------------------
    t_load_bq = BigQueryInsertJobOperator(
    task_id="load_to_bq",
    gcp_conn_id=GCP_CONN_ID,
    configuration={
        "load": {
            "sourceUris": [f"gs://{GCS_BUCKET}/silver/*.parquet"],
            "destinationTable": {
                "projectId": PROJECT_ID,
                "datasetId": "cdp_demo",
                "tableId": "transactions",
            },
            "sourceFormat": "PARQUET",
            "writeDisposition": "WRITE_TRUNCATE",
            "autodetect": True,
        }
    },
    location="asia-southeast1",
)

    t_upload >> t_bronze_to_parquet >> t_silver >> t_push_gcs >> t_load_bq