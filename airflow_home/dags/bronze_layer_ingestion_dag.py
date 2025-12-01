from __future__ import annotations
import os
import logging
from datetime import timedelta

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.exceptions import AirflowFailException

log = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "tan",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "admin123")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_BUCKET_BRONZE = "bronze-landing"
DATA_PREFIX_BRONZE = "customers"
DATA_PREFIX_TX = "transactions"

with DAG(
    dag_id="demo_bronze_layer_ingestion",
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

        client = Minio(MINIO_ENDPOINT, access_key=MINIO_ROOT_USER, secret_key=MINIO_ROOT_PASSWORD, secure=False)

        for b in (MINIO_BUCKET_BRONZE):
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

    t_upload_to_minio