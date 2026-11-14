import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def setting(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)


def table_name(table: str) -> str:
    allowed = {"daily_waste_summary", "category_waste_summary", "monthly_waste_summary", "stg_food_waste"}
    if table not in allowed:
        raise ValueError("Unknown analytics table")
    project = setting("GCP_PROJECT_ID")
    dataset = setting("BIGQUERY_ANALYTICS_DATASET", "food_waste_analytics")
    if not project:
        raise RuntimeError("Set GCP_PROJECT_ID in .env before connecting to BigQuery.")
    return f"`{project}.{dataset}.{table}`"
