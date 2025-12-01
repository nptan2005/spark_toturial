from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.hooks.base import BaseHook
from datetime import datetime

default_args = {
    "owner": "tan",
    "depends_on_past": False,
}

with DAG(
    dag_id="load_flights_to_postgres",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,  # chạy manual trước
    catchup=False,
    default_args=default_args,
) as dag:

    # STEP 1: TRUNCATE table trước khi load
    # (đoạn này bạn đã chuyển sang dùng hook rồi và OK, nên mình không đụng)
    from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

    truncate_table = SQLExecuteQueryOperator(
        task_id="truncate_flights",
        conn_id="postgres_dwh",
        sql="TRUNCATE TABLE flights;",
    )

    # STEP 2: Chạy spark-submit
    run_spark_job = BashOperator(
        task_id="spark_load_flights",
        bash_command="""
            /opt/spark/bin/spark-submit \
                --master spark://spark-master:7077 \
                --executor-memory 1g \
                --driver-memory 1g \
                --jars /opt/spark/jars/postgresql.jar \
                /opt/airflow/scripts/etl/load_flights_scripts.py
        """,
    )

    truncate_table >> run_spark_job

# kiem tra lỗi Broken DAG:
# docker compose exec airflow-scheduler bash
# airflow dags list-import-errors