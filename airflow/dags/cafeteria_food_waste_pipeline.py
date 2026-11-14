"""Orchestrate Airbyte sync, dbt transformations/tests, then warehouse validation."""
from __future__ import annotations

import os
from datetime import timedelta
from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.sensors.python import PythonSensor
from airflow.utils.dates import days_ago
from airbyte_api import AirbyteAPI


def trigger_airbyte_sync(**context) -> str:
    return AirbyteAPI().trigger_sync()


def airbyte_sync_finished(**context) -> bool:
    job_id = context["ti"].xcom_pull(task_ids="trigger_airbyte_sync")
    status = AirbyteAPI().job_status(str(job_id))
    if status in {"SUCCEEDED", "COMPLETED"}:
        return True
    if status in {"FAILED", "CANCELLED", "INCOMPLETE"}:
        raise AirflowException(f"Airbyte job {job_id} finished with status {status}")
    return False


def validate_analytics(**_context) -> None:
    from google.cloud import bigquery

    project = os.environ["GCP_PROJECT_ID"]
    dataset = os.getenv("BIGQUERY_ANALYTICS_DATASET", "food_waste_analytics")
    client = bigquery.Client(project=project)
    for table in ("daily_waste_summary", "category_waste_summary", "monthly_waste_summary"):
        table_id = f"{project}.{dataset}.{table}"
        try:
            count = next(client.query(f"SELECT COUNT(*) AS n FROM `{table_id}`").result()).n
        except Exception as exc:
            raise AirflowException(f"Could not validate analytics table {table_id}: {exc}") from exc
        if count < 1:
            raise AirflowException(f"Analytics table {table_id} contains no rows")


with DAG(
    dag_id="cafeteria_food_waste_pipeline",
    description="Airbyte to BigQuery raw, dbt models and tests, warehouse validation",
    start_date=days_ago(1),
    schedule="@daily",
    catchup=False,
    default_args={"owner": "data-engineering", "retries": 2, "retry_delay": timedelta(minutes=3)},
    dagrun_timeout=timedelta(hours=2),
    tags=["cafeteria", "bigquery", "dbt"],
) as dag:
    trigger = PythonOperator(task_id="trigger_airbyte_sync", python_callable=trigger_airbyte_sync)
    wait = PythonSensor(
        task_id="wait_for_airbyte_sync",
        python_callable=airbyte_sync_finished,
        mode="reschedule",
        poke_interval=30,
        timeout=60 * 60,
    )
    dbt_run = BashOperator(
        task_id="dbt_build",
        bash_command="cd /opt/food-waste/dbt && dbt build --profiles-dir /home/airflow/.dbt",
        append_env=True,
        execution_timeout=timedelta(minutes=45),
    )
    validate = PythonOperator(task_id="validate_analytics_tables", python_callable=validate_analytics)
    trigger >> wait >> dbt_run >> validate
