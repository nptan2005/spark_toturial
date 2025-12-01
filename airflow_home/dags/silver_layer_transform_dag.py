from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime

HADOOP_AWS_JAR = "/opt/spark/jars/hadoop-aws-3.3.4.jar"
AWS_SDK_JAR = "/opt/spark/jars/aws-java-sdk-bundle-1.12.548.jar"

with DAG(
    dag_id='silver_layer_transform_dag',
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['cdp', 'silver'],
) as dag:
    
    transform_customers = SparkSubmitOperator(
        task_id='transform_and_deduplicate_customers',
        application='/opt/airflow/scripts/transform_to_silver.py', # Sửa đường dẫn thực tế
        conn_id='spark_default', # Đảm bảo Airflow Connection Spark đã được cấu hình
        # Cấu hình phụ thuộc vào Spark Environment của bạn (ví dụ: Master/MinIO config)
        conf={
            "spark.jars": f"{HADOOP_AWS_JAR},{AWS_SDK_JAR}",
        },
    )