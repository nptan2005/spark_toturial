from datetime import datetime, timedelta

import boto3
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator


# 1. Hàm kiểm tra file trên MinIO
def check_minio_file():
    s3 = boto3.client(
        "s3",
        endpoint_url="http://localhost:9001",
        aws_access_key_id="admin",
        aws_secret_access_key="admin123"
    )
    result = s3.list_objects_v2(Bucket="demo-bucket", Prefix="output/result.csv")
    if "Contents" not in result:
        raise ValueError("Result not found yet!")
    print("Result file found in MinIO.")

# 2. DAG definition
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

dag = DAG(
    "spark_minio_demo",
    default_args=default_args,
    description="Demo DAG: Spark job + MinIO",
    schedule_interval=None,
    start_date=datetime(2025, 11, 10),
    catchup=False,
)

# 3. SparkSubmitOperator
spark_task = SparkSubmitOperator(
    task_id="spark_minio_task",
    application="/opt/airflow/dags/notebooks/spark_minio_demo.py",  # convert notebook -> py hoặc dùng .py script
    name="spark_minio_demo",
    conn_id="spark_default",
    verbose=True,
    dag=dag,
)

# 4. PythonOperator: kiểm tra kết quả trên MinIO
check_task = PythonOperator(
    task_id="check_minio_result",
    python_callable=check_minio_file,
    dag=dag
)

spark_task >> check_task
