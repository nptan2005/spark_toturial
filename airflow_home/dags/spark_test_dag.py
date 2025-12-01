from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    "spark_test",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
):

    run_spark = BashOperator(
        task_id="run_spark_job",
        bash_command="""
            /opt/spark/bin/spark-submit \
                --master spark://spark-master:7077 \
                /opt/airflow/scripts/etl/spark_test.py
        """,
        env={
            "JAVA_HOME": "/usr/lib/jvm/java-17-openjdk-arm64",
            "SPARK_HOME": "/opt/spark",
            "PATH": "/opt/spark/bin:/home/airflow/.local/bin:/usr/local/bin:/usr/bin:/bin"
        },
    )