from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable
from datetime import datetime, timedelta
import os

# ==============================
#      CONFIG (Enterprise++)
# ==============================

# Default parameters
DEFAULT_ETL_DIR = "/opt/airflow/scripts"
DEFAULT_SPARK_FILE = "etl/load_flights_scripts.py"
DEFAULT_INPUT_FILE = "/data/flights-larger.csv"
DEFAULT_TABLE = "flights"
DEFAULT_JARS = "/opt/spark/jars/postgresql.jar"

# Airflow Variables (optional override)
ETL_DIR = Variable.get("etl_dir", default_var=DEFAULT_ETL_DIR)
SPARK_SCRIPT = Variable.get("spark_script", default_var=DEFAULT_SPARK_FILE)
INPUT_FILE = Variable.get("input_file", default_var=DEFAULT_INPUT_FILE)
TARGET_TABLE = Variable.get("flights_target_table", default_var=DEFAULT_TABLE)
POSTGRES_JAR = Variable.get("postgres_jar", default_var=DEFAULT_JARS)

SPARK_EXECUTOR_MEMORY = Variable.get("spark_executor_mem", default_var="2g")
SPARK_DRIVER_MEMORY = Variable.get("spark_driver_mem", default_var="1g")


# ==============================
#     Python Callbacks
# ==============================

def truncate_table():
    hook = PostgresHook(postgres_conn_id="postgres_dwh")
    hook.run(f"TRUNCATE TABLE {TARGET_TABLE};")

def verify_data():
    hook = PostgresHook(postgres_conn_id="postgres_dwh")
    result = hook.get_first(f"SELECT COUNT(*) FROM {TARGET_TABLE};")
    print(f"📌 Rows in {TARGET_TABLE}: {result[0]}")


# ==============================
#           DAG
# ==============================

default_args = {
    "owner": "tan",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(seconds=60),
}

with DAG(
    dag_id="load_flights_to_postgres_enterprise",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    default_args=default_args,
    tags=["dwh", "spark", "enterprise", "postgres"],
) as dag:

    # ============== PRE-CHECK GROUP ==============
    with TaskGroup("pre_checks") as pre_checks:

        check_input_file = BashOperator(
            task_id="check_input_file",
            bash_command=f"""
                echo "Checking input file: {INPUT_FILE}"
                if [ ! -f {INPUT_FILE} ]; then
                    echo "❌ ERROR: File {INPUT_FILE} not found!"
                    exit 1
                fi
                echo "✓ Input file OK"
            """
        )

        truncate_task = PythonOperator(
            task_id="truncate_target_table",
            python_callable=truncate_table,
        )

        check_input_file >> truncate_task

    # ============== SPARK LOAD STEP ==============
    run_spark = BashOperator(
        task_id="run_spark_etl",
        bash_command=f"""
            echo ">>> Starting Spark ETL"
            FILE_PATH="{ETL_DIR}/{SPARK_SCRIPT}"
            
            if [ ! -f $FILE_PATH ]; then
                echo "❌ Spark script not found: $FILE_PATH"
                exit 1
            fi
            
            /opt/spark/bin/spark-submit \
                --master spark://spark-master:7077 \
                --executor-memory {SPARK_EXECUTOR_MEMORY} \
                --driver-memory {SPARK_DRIVER_MEMORY} \
                --jars {POSTGRES_JAR} \
                $FILE_PATH

            code=$?
            if [ $code -ne 0 ]; then
                echo "❌ Spark job failed with code $code"
                exit $code
            fi

            echo "✓ Spark job completed successfully."
        """
    )

    # ============== VERIFY LOADED DATA ==============
    verify = PythonOperator(
        task_id="verify_data_quality",
        python_callable=verify_data,
    )

    pre_checks >> run_spark >> verify