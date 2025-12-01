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

# ============= CONFIG =============
DEFAULT_ETL_SCRIPT = "/opt/airflow/scripts/etl/visa_ep733f_spark_etl.py"
DEFAULT_INPUT_FILE = "/data/visa_ep/20251103_EP733F_Masked.TXT"
DEFAULT_TABLE = "VISA_EP733F"
DEFAULT_JARS = "/opt/spark/jars/postgresql.jar"

EP_INPUT_PATH = Variable.get("visa_ep733f_input_file", default_var=DEFAULT_INPUT_FILE)
SPARK_SCRIPT = Variable.get("visa_ep733f_spark_script", default_var=DEFAULT_ETL_SCRIPT)
TARGET_TABLE = Variable.get("visa_ep733f_target_table", default_var=DEFAULT_TABLE)

# JDBC config -> lấy từ env / Variables
JDBC_URL = Variable.get(
    "visa_ep733f_jdbc_url",
    default_var="jdbc:postgresql://postgres-dwh:5432/dwhdb",
)
JDBC_USER = Variable.get("visa_ep733f_jdbc_user", default_var="dwh")
JDBC_PASSWORD = Variable.get("visa_ep733f_jdbc_password", default_var="dwh123")

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

def truncate_target():
    hook = PostgresHook(postgres_conn_id="postgres_dwh")
    hook.run(f"TRUNCATE TABLE {TARGET_TABLE};")
    print(f"Truncated table {TARGET_TABLE}")


def verify_data_hook(**context):
    hook = PostgresHook(postgres_conn_id="postgres_dwh")
    rows = hook.get_first(f"SELECT COUNT(*) FROM {TARGET_TABLE};")
    total = rows[0] if rows else 0
    print(f"Total records in {TARGET_TABLE}: {total}")
    context["ti"].xcom_push(key="rows_in_table", value=total)


def push_log_to_minio(**context):
    ti = context["ti"]
    dag_id = ti.dag_id
    task_id = ti.task_id
    run_id = ti.run_id
    exec_date = context["ds"]
    try_number = ti.try_number

    rows_in_table = ti.xcom_pull(
        key="rows_in_table", task_ids="verify_load", default=0
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
        f"visa_ep733f/{dag_id}/{exec_date}/"
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
    dag_id="visa_ep733f_import",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,   # sau này set cron: "0 6 * * *" chẳng hạn
    catchup=False,
    default_args=default_args,
    tags=["spark", "postgres", "visa", "ep733f", "minio", "teams"],
    on_failure_callback=notify_teams_failure,
) as dag:

    with TaskGroup("pre_checks") as pre_checks:

        validate_input_file = BashOperator(
            task_id="validate_input_file",
            bash_command=f"""
                if [ ! -f "{EP_INPUT_PATH}" ]; then
                    echo "❌ EP733F file not found: {EP_INPUT_PATH}";
                    exit 1;
                fi
                echo "✓ Input file OK: {EP_INPUT_PATH}"
            """,
        )

        truncate_task = PythonOperator(
            task_id="truncate_target_table",
            python_callable=truncate_target,
        )

        validate_input_file >> truncate_task

    run_spark_job = BashOperator(
        task_id="spark_import_ep733f",
        bash_command=f"""
            echo ">>> Running Spark Job EP733F..."
            /opt/spark/bin/spark-submit \
                --master spark://spark-master:7077 \
                --executor-memory 2g \
                --driver-memory 1g \
                --jars /opt/spark/jars/postgresql.jar \
                {SPARK_SCRIPT} "{EP_INPUT_PATH}" "{JDBC_URL}" "{TARGET_TABLE}" "{JDBC_USER}" "{JDBC_PASSWORD}"

            EXIT_CODE=$?
            if [ $EXIT_CODE -ne 0 ]; then
                echo "❌ Spark job failed! Exit code: $EXIT_CODE"
                exit $EXIT_CODE
            fi

            echo "✓ Spark job completed."
        """,
    )

    verify_data = PythonOperator(
        task_id="verify_load",
        python_callable=verify_data_hook,
        provide_context=True,
    )

    log_to_minio = PythonOperator(
        task_id="log_to_minio",
        python_callable=push_log_to_minio,
        provide_context=True,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    notify_teams = PythonOperator(
        task_id="notify_teams_on_failure",
        python_callable=notify_teams_failure,
        provide_context=True,
        trigger_rule=TriggerRule.ONE_FAILED,
    )

    pre_checks >> run_spark_job >> verify_data >> log_to_minio
    [pre_checks, run_spark_job, verify_data, log_to_minio] >> notify_teams