# /opt/airflow/dags/test_spark_submit.py
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    "test_spark_submit",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:

    spark_test = BashOperator(
        task_id="spark_test",
        bash_command="""
            /opt/spark/bin/spark-submit \
                --master spark://spark-master:7077 \
                /opt/airflow/scripts/etl/hello_spark.py
        """
    )