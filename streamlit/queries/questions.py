from dataclasses import dataclass

from google.cloud import bigquery

from utils.config import table_name


@dataclass(frozen=True)
class Question:
    label: str
    sql: str
    chart: str | None = None


def supported_questions() -> list[Question]:
    daily, category = table_name("daily_waste_summary"), table_name("category_waste_summary")
    monthly = table_name("monthly_waste_summary")
    return [
        Question("Which food category contributes the highest amount of food waste?", f"SELECT waste_category, total_food_waste_kg, percent_of_total_waste FROM {category} ORDER BY total_food_waste_kg DESC LIMIT 1", "bar"),
        Question("How much food waste is generated each day?", f"SELECT waste_date, total_food_waste_kg FROM {daily} ORDER BY waste_date", "line"),
        Question("Which month recorded the highest food waste?", f"SELECT waste_month, total_food_waste_kg FROM {monthly} ORDER BY total_food_waste_kg DESC LIMIT 1", "bar"),
        Question("What is the average food waste per meal?", f"SELECT SAFE_DIVIDE(SUM(total_food_waste_kg), SUM(total_meals_served)) AS average_food_waste_per_meal_kg FROM {daily}", None),
        Question("Does meal demand correspond to changes in food waste?", f"SELECT total_meals_served, total_food_waste_kg, waste_date FROM {daily} ORDER BY waste_date", "scatter"),
        Question("How does temperature relate to food waste?", f"SELECT average_temperature_c, total_food_waste_kg, waste_date FROM {daily} WHERE average_temperature_c IS NOT NULL ORDER BY waste_date", "scatter"),
    ]


def execute_question(question: Question):
    from utils.bigquery_client import get_client
    return get_client().query(question.sql, job_config=bigquery.QueryJobConfig()).to_dataframe()
