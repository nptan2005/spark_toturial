# oracle_to_dwh_dag.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.python import PythonOperator
import os
from pathlib import Path

default_args = {
    "owner": "tan",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2)
}

dag = DAG(
    dag_id="oracle_to_dwh_full_pipeline",
    default_args=default_args,
    schedule_interval="@hourly",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1
)

# 1) Extract from Oracle using spark-submit
spark_extract = SparkSubmitOperator(
    task_id="spark_extract_oracle_to_parquet",
    application="/opt/airflow/jobs/oracle_to_parquet.py",  # mount file to image or shared volume
    name="oracle_to_parquet",
    application_args=[],
    conf={"spark.driver.memory": "1g"},
    conn_id=None,
    dag=dag,
)

# 2) Transform & load to Postgres DWH via spark
spark_load = SparkSubmitOperator(
    task_id="spark_parquet_to_postgres",
    application="/opt/airflow/jobs/parquet_to_postgres.py",
    name="parquet_to_postgres",
    conf={"spark.driver.memory": "1g"},
    dag=dag,
)

# 3) Optional: push realtime sample messages to Kafka
def produce_realtime():
    from subprocess import check_call
    # We assume kafka_producer.py exists on the airflow container or mounted dir
    check_call(["python3", "/opt/airflow/scripts/kafka_producer.py"])

kafka_push = PythonOperator(
    task_id="produce_realtime_to_kafka",
    python_callable=produce_realtime,
    dag=dag
)

# Basic DAG flow: batch ETL first, then produce realtime sample
spark_extract >> spark_load
spark_load >> kafka_push