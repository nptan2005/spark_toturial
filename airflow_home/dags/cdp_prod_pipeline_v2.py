# dags/cdp_prod_pipeline_v2.py
"""
Airflow DAG: cdp_prod_pipeline_v2
Pipeline:
 - upload demo -> minio (optional)
 - bronze ingest (customers + transactions)  [Spark submit]
 - silver transform (customers + transactions) [Spark submit]
 - gold build (join) [Spark submit]
 - push gold to GCS (PythonOperator)
 - load to BigQuery (BigQueryInsertJobOperator) (one job per table)
Features:
 - retries, retry_delay, email_on_failure (env)
 - XCom metadata (run_id, batch_id)
 - simple lineage via xcom push file lists / counts
"""
from __future__ import annotations
import os
import logging
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule
from airflow.models import Variable

log = logging.getLogger(__name__)

# --- Configs (env or Airflow Variables)
MINIO_ENDPOINT_RAW = os.getenv("MINIO_ENDPOINT", Variable.get("MINIO_ENDPOINT", "minio:9000"))
MINIO_S3A_ENDPOINT = os.getenv("MINIO_S3A_ENDPOINT", Variable.get("MINIO_S3A_ENDPOINT", "http://minio:9000"))
MINIO_BUCKET_BRONZE = os.getenv("MINIO_BRONZE_BUCKET", Variable.get("MINIO_BRONZE_BUCKET", "bronze"))
MINIO_BUCKET_SILVER = os.getenv("MINIO_SILVER_BUCKET", Variable.get("MINIO_SILVER_BUCKET", "silver"))
MINIO_BUCKET_GOLD = os.getenv("MINIO_GOLD_BUCKET", Variable.get("MINIO_GOLD_BUCKET", "gold"))
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", Variable.get("MINIO_ROOT_USER", "admin"))
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", Variable.get("MINIO_ROOT_PASSWORD", "admin123"))

SPARK_MASTER = os.getenv("SPARK_MASTER", "spark://spark-master:7077")
SPARK_BIN = os.getenv("SPARK_BIN", "/opt/spark/bin/spark-submit")
SPARK_JARS = os.getenv("SPARK_JARS", "/opt/spark/jars/hadoop-aws-3.3.4.jar,/opt/spark/jars/aws-java-sdk-bundle-1.12.548.jar")

# GCP
GCS_BUCKET = os.getenv("GCS_BUCKET", Variable.get("GCS_BUCKET", "my-cdp-demo-bucket-123"))
GCP_CONN_ID = os.getenv("GCP_CONN_ID", "google_cloud_default")
PROJECT_ID = os.getenv("PROJECT_ID", Variable.get("PROJECT_ID", "my-cdp-demo-01"))
BQ_DATASET = os.getenv("BQ_DATASET", Variable.get("BQ_DATASET", "cdp_demo"))

DEFAULT_ARGS = {
    "owner": "tan",
    "depends_on_past": False,
    "email_on_failure": True,
    "email": os.getenv("ALERT_EMAIL", Variable.get("ALERT_EMAIL", "")),
    "retries": int(os.getenv("RETRIES", 1)),
    "retry_delay": timedelta(minutes=5),
}

def spark_submit_cmd(script_path, extra_args=""):
    return f"""{SPARK_BIN} \
      --master {SPARK_MASTER} \
      --conf spark.hadoop.fs.s3a.endpoint={MINIO_S3A_ENDPOINT} \
      --conf spark.hadoop.fs.s3a.access.key={MINIO_ROOT_USER} \
      --conf spark.hadoop.fs.s3a.secret.key={MINIO_ROOT_PASSWORD} \
      --conf spark.hadoop.fs.s3a.path.style.access=true \
      --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false \
      --jars {SPARK_JARS} \
      {script_path} {extra_args}
    """

def push_dir_to_gcs(minio_bucket, prefix, gcs_dest_prefix, tmp_dir="/tmp/cdp_gcs_upload"):
    from minio import Minio
    import tempfile, shutil, pathlib, os
    client = Minio(MINIO_ENDPOINT_RAW,
                   access_key=MINIO_ROOT_USER,
                   secret_key=MINIO_ROOT_PASSWORD,
                   secure=False)
    tmp = pathlib.Path(tempfile.mkdtemp(dir="/tmp"))
    # download all parquet under prefix
    for obj in client.list_objects(minio_bucket, prefix, recursive=True):
        dest = tmp / obj.object_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        client.fget_object(minio_bucket, obj.object_name, str(dest))
    # upload to GCS
    gcs = GCSHook(gcp_conn_id=GCP_CONN_ID)
    for f in tmp.rglob("*.parquet"):
        # use simple name or preserve path
        rel = f.relative_to(tmp)
        gcs_path = f"{gcs_dest_prefix}/{rel.as_posix()}"
        gcs.upload(GCS_BUCKET, gcs_path, str(f))
    shutil.rmtree(tmp)
    return True

with DAG(
    "cdp_prod_pipeline_v2",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["cdp", "prod", "v2"],
) as dag:

    # optionally upload demo files to minio
    def upload_demo():
        from minio import Minio
        import pathlib
        client = Minio(MINIO_ENDPOINT_RAW,
                       access_key=MINIO_ROOT_USER,
                       secret_key=MINIO_ROOT_PASSWORD,
                       secure=False)
        base = pathlib.Path("/data/demo2")
        client.fput_object(MINIO_BUCKET_BRONZE, "customers/customers.csv", base/"customers.csv")
        client.fput_object(MINIO_BUCKET_BRONZE, "transactions/transactions.csv", base/"transactions.csv")
    t_upload_demo = PythonOperator(task_id="upload_demo_to_minio", python_callable=upload_demo)

    # Bronze ingest customers
    t_bronze_customers = BashOperator(
        task_id="bronze_ingest_customers",
        bash_command=spark_submit_cmd(
            "/opt/spark/jobs/bronze/bronze_ingest.py",
            f""" --minio-endpoint {MINIO_S3A_ENDPOINT} --minio-access-key {MINIO_ROOT_USER} --minio-secret-key {MINIO_ROOT_PASSWORD} --bronze-bucket {MINIO_BUCKET_BRONZE} --dataset customers"""
        )
    )

    # Bronze ingest transactions
    t_bronze_tx = BashOperator(
        task_id="bronze_ingest_transactions",
        bash_command=spark_submit_cmd(
            "/opt/spark/jobs/bronze/bronze_ingest.py",
            f""" --minio-endpoint {MINIO_S3A_ENDPOINT} --minio-access-key {MINIO_ROOT_USER} --minio-secret-key {MINIO_ROOT_PASSWORD} --bronze-bucket {MINIO_BUCKET_BRONZE} --dataset transactions"""
        )
    )

    # Silver transform customers
    t_silver_customers = BashOperator(
        task_id="silver_transform_customers",
        bash_command=spark_submit_cmd(
            "/opt/spark/jobs/silver/transform_silver.py",
            f""" --minio-endpoint {MINIO_S3A_ENDPOINT} --minio-access-key {MINIO_ROOT_USER} --minio-secret-key {MINIO_ROOT_PASSWORD} --bronze-bucket {MINIO_BUCKET_BRONZE} --silver-bucket {MINIO_BUCKET_SILVER} --dataset customers"""
        )
    )

    # Silver transform transactions
    t_silver_tx = BashOperator(
        task_id="silver_transform_transactions",
        bash_command=spark_submit_cmd(
            "/opt/spark/jobs/silver/transform_silver.py",
            f""" --minio-endpoint {MINIO_S3A_ENDPOINT} --minio-access-key {MINIO_ROOT_USER} --minio-secret-key {MINIO_ROOT_PASSWORD} --bronze-bucket {MINIO_BUCKET_BRONZE} --silver-bucket {MINIO_BUCKET_SILVER} --dataset transactions"""
        )
    )

    # Gold build (join)
    t_gold_build = BashOperator(
        task_id="gold_build",
        bash_command=spark_submit_cmd(
            "/opt/spark/jobs/gold/gold_build.py",
            f""" --minio-endpoint {MINIO_S3A_ENDPOINT} --minio-access-key {MINIO_ROOT_USER} --minio-secret-key {MINIO_ROOT_PASSWORD} --silver-bucket {MINIO_BUCKET_SILVER} --gold-bucket {MINIO_BUCKET_GOLD}"""
        ),
        retries=1,
        retry_delay=timedelta(minutes=5),
    )

    # Push gold parquet to GCS
    def push_gold_to_gcs():
        # push gold/dim_customer and gold/fact_transactions
        push_dir_to_gcs(MINIO_BUCKET_GOLD, "parquet/dim_customer", "gold/dim_customer")
        push_dir_to_gcs(MINIO_BUCKET_GOLD, "parquet/fact_transactions", "gold/fact_transactions")
    t_push_gcs = PythonOperator(task_id="push_gold_to_gcs", python_callable=push_gold_to_gcs)

    # Load to BigQuery: dim_customer
    t_load_bq_dim = BigQueryInsertJobOperator(
        task_id="load_bq_dim_customer",
        gcp_conn_id=GCP_CONN_ID,
        configuration={
            "load": {
                "sourceUris": [f"gs://{GCS_BUCKET}/gold/dim_customer/*.parquet"],
                "destinationTable": {
                    "projectId": PROJECT_ID,
                    "datasetId": BQ_DATASET,
                    "tableId": "dim_customer",
                },
                "sourceFormat": "PARQUET",
                "writeDisposition": "WRITE_TRUNCATE",
                "autodetect": True,
            }
        },
        location="asia-southeast1",
    )

    # Load to BigQuery: fact_transactions
    t_load_bq_fact = BigQueryInsertJobOperator(
        task_id="load_bq_fact_transactions",
        gcp_conn_id=GCP_CONN_ID,
        configuration={
            "load": {
                "sourceUris": [f"gs://{GCS_BUCKET}/gold/fact_transactions/*.parquet"],
                "destinationTable": {
                    "projectId": PROJECT_ID,
                    "datasetId": BQ_DATASET,
                    "tableId": "fact_transactions",
                },
                "sourceFormat": "PARQUET",
                "writeDisposition": "WRITE_TRUNCATE",
                "autodetect": True,
            }
        },
        location="asia-southeast1",
    )

    # DAG dependencies
    # cach 1:
    # upload → bronze
    # for t in [t_bronze_customers, t_bronze_tx]:
    #     t_upload_demo >> t

    # # bronze → silver
    # for src in [t_bronze_customers, t_bronze_tx]:
    #     for dst in [t_silver_customers, t_silver_tx]:
    #         src >> dst

    # # silver → gold
    # for t in [t_silver_customers, t_silver_tx]:
    #     t >> t_gold_build

    # # gold → push_gcs
    # t_gold_build >> t_push_gcs

    # # push_gcs → load BQ
    # for t in [t_load_bq_dim, t_load_bq_fact]:
    #     t_push_gcs >> t


    # cach 2:
    with TaskGroup("bronze") as bronze_group:
        t_bronze_customers
        t_bronze_tx

    with TaskGroup("silver") as silver_group:
        t_silver_customers
        t_silver_tx

    t_upload_demo >> bronze_group >> silver_group >> t_gold_build >> t_push_gcs >> [t_load_bq_dim, t_load_bq_fact]