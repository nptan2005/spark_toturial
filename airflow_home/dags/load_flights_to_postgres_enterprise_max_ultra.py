# /opt/airflow/dags/load_flights_to_postgres_enterprise_max_ultra.py

from datetime import datetime, timedelta
import json
import os

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule

import boto3
import requests

# ============= CONFIG (có thể override bằng Airflow Variables) =============
DEFAULT_ETL_DIR = "/opt/airflow/scripts/etl"
DEFAULT_SPARK_FILE = "load_flights_scripts.py"
DEFAULT_INPUT_FILE = "/data/flights-larger.csv"
DEFAULT_TABLE = "flights"
DEFAULT_JARS = "/opt/spark/jars/postgresql.jar"

CSV_PATH = Variable.get("input_file", default_var=DEFAULT_INPUT_FILE)
ETL_DIR = Variable.get("etl_dir", default_var=DEFAULT_ETL_DIR)
SCRIPT = Variable.get(
    "spark_script",
    default_var=DEFAULT_SPARK_FILE,
)
SPARK_SCRIPT = os.path.join(ETL_DIR, SCRIPT)
TARGET_TABLE = Variable.get("flights_target_table", default_var=DEFAULT_TABLE)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_BUCKET = os.getenv("MINIO_LOG_BUCKET", "airflow-logs")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "admin123")

MS_TEAMS_WEBHOOK = os.getenv("MS_TEAMS_WEBHOOK")

default_args = {
    "owner": "tan",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

# ========================== PYTHON CALLABLES ===============================

def truncate_flights_hook():
    """TRUNCATE bảng flights trước khi load."""
    hook = PostgresHook(postgres_conn_id="postgres_dwh")
    hook.run(f"TRUNCATE TABLE {TARGET_TABLE};")
    print(f"Truncated table {TARGET_TABLE}")


def verify_data_hook(**context):
    """Check số record trong bảng sau khi load."""
    hook = PostgresHook(postgres_conn_id="postgres_dwh")
    rows = hook.get_first(f"SELECT COUNT(*) FROM {TARGET_TABLE};")
    total = rows[0] if rows else 0
    print(f"Total records in {TARGET_TABLE}: {total}")
    # push XCom để task log sử dụng
    context["ti"].xcom_push(key="rows_in_table", value=total)


def push_log_to_minio(**context):
    """Ghi log JSON lên MinIO (S3-compatible)."""
    ti = context["ti"]

    dag_id = ti.dag_id
    task_id = ti.task_id
    run_id = ti.run_id
    exec_date = context["ds"]
    try_number = ti.try_number

    rows_in_table = ti.xcom_pull(
        key="rows_in_table",
        task_ids="verify_load",
        default=0,
    )

    log_data = {
        "dag_id": dag_id,
        "task_id": task_id,
        "run_id": run_id,
        "execution_date": exec_date,
        "try_number": try_number,
        "target_table": TARGET_TABLE,
        "rows_in_table": rows_in_table,
        "status": "SUCCESS" if ti.state == "success" else str(ti.state),
    }

    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1",
    )

    key = (
        f"airflow/{dag_id}/{exec_date}/"
        f"{task_id}_run={run_id.replace(':', '_')}_try={try_number}.json"
    )

    s3.put_object(
        Bucket=MINIO_BUCKET,
        Key=key,
        Body=json.dumps(log_data, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    print(f"Uploaded log to MinIO: s3://{MINIO_BUCKET}/{key}")


def notify_teams_failure(context):
    """Bắn message lên MS Teams nếu DAG / task fail."""
    if not MS_TEAMS_WEBHOOK:
        print("MS_TEAMS_WEBHOOK not set -> skip Teams notification")
        return

    ti = context["ti"]
    dag_id = ti.dag_id
    task_id = ti.task_id
    run_id = ti.run_id
    exec_date = context["ts"]

    base_url = os.getenv("AIRFLOW__WEBSERVER__BASE_URL", "http://localhost:8080")
    log_url = (
        f"{base_url}/log?dag_id={dag_id}"
        f"&task_id={task_id}&execution_date={exec_date}"
    )

    card = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": f"[Airflow] DAG {dag_id} failed",
        "themeColor": "FF0000",
        "title": f"❌ Airflow DAG FAILED: {dag_id}",
        "sections": [
            {
                "activityTitle": f"Task **{task_id}** failed",
                "activitySubtitle": f"Run ID: `{run_id}`",
                "text": f"Execution time: `{exec_date}`\n\n[Open log]({log_url})",
            }
        ],
    }

    resp = requests.post(
        MS_TEAMS_WEBHOOK,
        data=json.dumps(card),
        headers={"Content-Type": "application/json"},
        timeout=10,
    )

    print("Teams response:", resp.status_code, resp.text[:200])


# ================================ DAG ======================================

with DAG(
    dag_id="load_flights_to_postgres_enterprise_max_ultra",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    default_args=default_args,
    tags=["spark", "postgres", "enterprise", "dwh", "minio", "teams"],
) as dag:

    # === PRE-CHECK GROUP ===
    with TaskGroup("pre_checks") as pre_checks:

        validate_input_file = BashOperator(
            task_id="validate_input_file",
            bash_command=f"""
                if [ ! -f "{CSV_PATH}" ]; then
                    echo "❌ File input không tồn tại: {CSV_PATH}";
                    exit 1;
                fi
                echo "✓ Input file OK: {CSV_PATH}"
            """,
        )

        truncate_task = PythonOperator(
            task_id="truncate_flights",
            python_callable=truncate_flights_hook,
        )

        validate_input_file >> truncate_task

    # === SPARK EXECUTION ===
    run_spark_job = BashOperator(
        task_id="spark_load_flights",
        bash_command=f"""
            echo ">>> Running Spark Job..."
            /opt/spark/bin/spark-submit \
                --master spark://spark-master:7077 \
                --executor-memory 2g \
                --driver-memory 1g \
                --jars /opt/spark/jars/postgresql.jar \
                {SPARK_SCRIPT} "{CSV_PATH}" "{TARGET_TABLE}"

            EXIT_CODE=$?
            if [ $EXIT_CODE -ne 0 ]; then
                echo "❌ Spark job failed! Exit code: $EXIT_CODE"
                exit $EXIT_CODE
            fi

            echo "✓ Spark job completed."
        """,
    )

    # === VERIFY DATA ===
    verify_data = PythonOperator(
        task_id="verify_load",
        python_callable=verify_data_hook,
        provide_context=True,
    )

    # === LOG TO MINIO (chạy kể cả khi verify_data fail) ===
    log_to_minio = PythonOperator(
        task_id="log_to_minio",
        python_callable=push_log_to_minio,
        provide_context=True,
        trigger_rule=TriggerRule.ALL_DONE,  # luôn chạy, kể cả upstream fail
    )

    # === TEAMS NOTIFY (chỉ chạy khi có task fail) ===
    notify_teams = PythonOperator(
        task_id="notify_teams_on_failure",
        python_callable=notify_teams_failure,
        provide_context=True,
        trigger_rule=TriggerRule.ONE_FAILED,
    )

    # Flow tổng
    pre_checks >> run_spark_job >> verify_data >> log_to_minio
    [pre_checks, run_spark_job, verify_data, log_to_minio] >> notify_teams