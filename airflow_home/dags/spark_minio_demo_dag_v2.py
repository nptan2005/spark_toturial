from datetime import datetime, timedelta

import boto3
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator


def check_minio_file():
    s3 = boto3.client(
        "s3",
        endpoint_url="http://localhost:9001",
        aws_access_key_id="admin",
        aws_secret_access_key="admin123"
    )
    resp = s3.list_objects_v2(Bucket="demo-bucket", Prefix="output/")
    if "Contents" not in resp or len(resp["Contents"]) == 0:
        raise ValueError("Result file not found in MinIO")
    print("Result file exists in MinIO")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    "spark_minio_demo_2",
    default_args=default_args,
    description="Demo Spark job via Airflow, input from MinIO, output to MinIO",
    schedule_interval=None,
    start_date=datetime(2025,1,1),
    catchup=False
) as dag:

    spark_task = SparkSubmitOperator(
        task_id="spark_task",
        application="/opt/airflow/dags/spark_minio_demo_dag_v2.py",
        name="spark_minio_demo_2",
        conn_id="spark_default",
        verbose=True
    )

    check_task = PythonOperator(
        task_id="check_minio",
        python_callable=check_minio_file
    )

    spark_task >> check_task
