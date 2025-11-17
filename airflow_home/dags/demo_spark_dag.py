from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    "demo_spark_dag",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
):

    run_demo = BashOperator(
        task_id="run_demo",
        bash_command="""
            /opt/spark/bin/spark-submit \
                --master spark://spark-master:7077 \
                /opt/airflow/scripts/demo_spark_job.py
        """,
    )