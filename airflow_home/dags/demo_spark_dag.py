from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from pyspark.sql import SparkSession


def spark_job():
    spark = (
        SparkSession.builder.appName("AirflowSparkDemo")
        .master("spark://spark-master:7077")
        .getOrCreate()
    )
    data = [("Alice", 30), ("Bob", 25)]
    df = spark.createDataFrame(data, ["name", "age"])
    df.show()


with DAG(
    dag_id="demo_spark_dag",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:
    t1 = PythonOperator(task_id="run_spark_job", python_callable=spark_job)
