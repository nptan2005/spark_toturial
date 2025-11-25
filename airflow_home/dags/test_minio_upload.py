import os
import json
import boto3
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "admin123")
MINIO_BUCKET = "test"


def test_upload():
    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
    )

    obj = {
        "test": "minio connection OK",
        "timestamp": str(datetime.now()),
    }

    key = f"test/test-{datetime.now().strftime('%Y%m%d%H%M%S')}.json"

    s3.put_object(
        Bucket=MINIO_BUCKET,
        Key=key,
        Body=json.dumps(obj),
        ContentType="application/json"
    )

    print(f"Uploaded: s3://{MINIO_BUCKET}/{key}")


with DAG(
    "test_minio_upload",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:

    do_test = PythonOperator(
        task_id="upload_test",
        python_callable=test_upload
    )