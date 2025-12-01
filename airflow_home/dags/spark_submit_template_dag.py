from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

SPARK_MASTER = "spark://spark-master:7077"
SPARK_BIN = "/opt/spark/bin/spark-submit"
SPARK_SCRIPT = "/opt/airflow/scripts/spark_test.py"

default_args = {
    "owner": "tan",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(seconds=20),
    "execution_timeout": timedelta(minutes=5),   # Không để job treo
    "email_on_failure": False,
    "email_on_retry": False,
}

with DAG(
    dag_id="spark_submit_prod",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    schedule_interval=None,
    default_args=default_args,
    tags=["spark", "production"],
) as dag:

    spark_task = BashOperator(
        task_id="run_spark_job",
        bash_command=f"""
            echo "[INFO] Starting Spark job..."
            
            {SPARK_BIN} \
                --master {SPARK_MASTER} \
                --deploy-mode client \
                --executor-cores 1 \
                --total-executor-cores 1 \
                --executor-memory 1g \
                --driver-memory 1g \
                --conf spark.ui.showConsoleProgress=true \
                --conf spark.executor.heartbeatInterval=30s \
                --conf spark.network.timeout=120s \
                {SPARK_SCRIPT}

            EXIT_CODE=$?
            echo "[INFO] Spark job finished with exit code: $EXIT_CODE"
            exit $EXIT_CODE
        """,
        do_xcom_push=False,  # Không đẩy log khủng
    )