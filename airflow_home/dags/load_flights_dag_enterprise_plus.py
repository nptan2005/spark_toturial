from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

default_args = {
    "owner": "tan",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    # Sau này có thể thêm email/slack ở đây
    # "email": ["you@example.com"],
    # "email_on_failure": True,
}

with DAG(
    dag_id="load_flights_to_postgres_enterprise_plus",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,       # manual; sau này có thể đổi thành '0 2 * * *'
    catchup=False,
    default_args=default_args,
    max_active_runs=1,
    params={
        "spark_script": "/opt/airflow/scripts/etl/load_flights_scripts.py",
        "spark_master": "spark://spark-master:7077",
        "spark_jars": "/opt/spark/jars/postgresql.jar",
        # Cho phép override CSV path nếu sau này cần
        "csv_path": "/data/flights-larger.csv",
    },
    tags=["dwh", "spark", "postgres", "enterprise"],
) as dag:

    # 1️⃣ Truncate bảng flights
    truncate_table = SQLExecuteQueryOperator(
        task_id="truncate_flights",
        conn_id="postgres_dwh",
        sql="TRUNCATE TABLE flights;",
    )

    # 2️⃣ Spark: load CSV → Postgres
    # Bạn đã hard-code PATH trong script Spark,
    # nhưng ta vẫn truyền param để sau này nâng cấp source.
    spark_cmd = r"""
        echo "Starting Spark load job ..."
        echo "Using script: {{ params.spark_script }}"
        echo "Using CSV: {{ params.csv_path }}"

        /opt/spark/bin/spark-submit \
            --master {{ params.spark_master }} \
            --executor-memory 1g \
            --driver-memory 1g \
            --jars {{ params.spark_jars }} \
            {{ params.spark_script }}

        EXIT_CODE=$?
        echo "Spark job finished with code: ${EXIT_CODE}"
        exit ${EXIT_CODE}
    """

    run_spark_job = BashOperator(
        task_id="spark_load_flights",
        bash_command=spark_cmd,
    )

    truncate_table >> run_spark_job