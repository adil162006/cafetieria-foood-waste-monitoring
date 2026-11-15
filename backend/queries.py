"""Fixed BigQuery queries for the dashboard and its question selector."""
from __future__ import annotations

import os
import re
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from google.cloud import bigquery
from google.oauth2 import service_account


QUESTIONS: dict[str, tuple[str, str]] = {
    "highest_category": (
        "Which food category contributes the highest amount of food waste?",
        "SELECT waste_category, total_food_waste_kg, percent_of_total_waste "
        "FROM {category} ORDER BY total_food_waste_kg DESC LIMIT 1",
    ),
    "daily_waste": (
        "How much food waste is generated each day?",
        "SELECT waste_date, total_food_waste_kg FROM {daily} ORDER BY waste_date",
    ),
    "highest_month": (
        "Which month recorded the highest food waste?",
        "SELECT waste_month, total_food_waste_kg FROM {monthly} "
        "ORDER BY total_food_waste_kg DESC LIMIT 1",
    ),
    "waste_per_meal": (
        "What is the average food waste per meal?",
        "SELECT SAFE_DIVIDE(SUM(total_food_waste_kg), SUM(total_meals_served)) "
        "AS average_food_waste_per_meal_kg FROM {daily}",
    ),
    "demand_relation": (
        "Does meal demand correspond to changes in food waste?",
        "SELECT total_meals_served, total_food_waste_kg, waste_date "
        "FROM {daily} ORDER BY waste_date",
    ),
    "temperature_relation": (
        "How does temperature relate to food waste?",
        "SELECT average_temperature_c, total_food_waste_kg, waste_date "
        "FROM {daily} WHERE average_temperature_c IS NOT NULL ORDER BY waste_date",
    ),
}


def _identifier(name: str, default: str) -> str:
    value = os.getenv(name, default)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError(f"Invalid BigQuery identifier in {name}.")
    return value


def table_names() -> dict[str, str]:
    project = os.getenv("GCP_PROJECT_ID", "").strip()
    if not project:
        raise RuntimeError("Set GCP_PROJECT_ID in the workspace .env file.")
    project = _identifier("GCP_PROJECT_ID", project)
    dataset = _identifier("BIGQUERY_ANALYTICS_DATASET", "food_waste_analytics")
    prefix = f"`{project}.{dataset}"
    return {
        "daily": f"{prefix}.daily_waste_summary`",
        "category": f"{prefix}.category_waste_summary`",
        "monthly": f"{prefix}.monthly_waste_summary`",
    }


def get_client() -> bigquery.Client:
    project = os.getenv("GCP_PROJECT_ID", "").strip()
    if not project:
        raise RuntimeError("Set GCP_PROJECT_ID in the workspace .env file.")
    project = _identifier("GCP_PROJECT_ID", project)
    location = os.getenv("BIGQUERY_LOCATION", "US")
    key_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./servicekey.json")
    credentials = service_account.Credentials.from_service_account_file(key_file) if key_file else None
    return bigquery.Client(project=project, credentials=credentials, location=location)


def run_query(sql: str) -> list[dict[str, Any]]:
    """Return BigQuery API rows as plain JSON-safe Python values; no Arrow/pandas."""
    rows = get_client().query(sql).result()
    return [{key: _json_value(value) for key, value in row.items()} for row in rows]


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def dashboard_payload() -> dict[str, Any]:
    tables = table_names()
    daily, category, monthly = (tables[k] for k in ("daily", "category", "monthly"))
    kpis = run_query(
        f"SELECT SUM(total_food_waste_kg) AS total_waste, "
        f"SUM(total_meals_served) AS total_meals, "
        f"SAFE_DIVIDE(SUM(total_food_waste_kg), SUM(total_meals_served)) AS waste_per_meal "
        f"FROM {daily}"
    )
    return {
        "kpis": (kpis[0] if kpis else {}),
        "daily": run_query(
            f"SELECT waste_date, total_food_waste_kg, total_meals_served, "
            f"average_food_waste_per_meal_kg, average_temperature_c, record_count "
            f"FROM {daily} ORDER BY waste_date"
        ),
        "categories": run_query(
            f"SELECT waste_category, total_food_waste_kg, percent_of_total_waste "
            f"FROM {category} ORDER BY total_food_waste_kg DESC"
        ),
        "monthly": run_query(
            f"SELECT waste_month, total_food_waste_kg FROM {monthly} ORDER BY waste_month"
        ),
    }


def question_payload(question_id: str) -> dict[str, Any]:
    try:
        label, template = QUESTIONS[question_id]
    except KeyError as exc:
        raise ValueError("Choose one of the supported analytics questions.") from exc
    sql = template.format(**table_names())
    return {"id": question_id, "label": label, "sql": sql, "rows": run_query(sql)}
