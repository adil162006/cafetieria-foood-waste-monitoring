import os
import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import queries


class DashboardQueryTests(unittest.TestCase):
    @patch.dict(os.environ, {"GCP_PROJECT_ID": "demo-project", "BIGQUERY_ANALYTICS_DATASET": "food_waste_analytics"})
    def test_table_identifiers_are_centralized_and_quoted(self):
        tables = queries.table_names()
        self.assertEqual(tables["daily"], "`demo-project.food_waste_analytics.daily_waste_summary`")
        self.assertTrue(all(value.startswith("`") and value.endswith("`") for value in tables.values()))

    @patch.dict(os.environ, {"GCP_PROJECT_ID": "demo-project"})
    def test_question_sql_is_predefined_and_uses_analytics_tables(self):
        self.assertEqual(len(queries.QUESTIONS), 6)
        for question_id in queries.QUESTIONS:
            with self.subTest(question_id=question_id), patch.object(queries, "run_query", return_value=[]):
                payload = queries.question_payload(question_id)
                self.assertIn("demo-project.food_waste_analytics", payload["sql"])
                self.assertNotIn(";", payload["sql"])
                self.assertEqual(payload["id"], question_id)

    def test_unsupported_questions_are_rejected(self):
        with self.assertRaises(ValueError):
            queries.question_payload("SELECT * FROM anything")

    def test_bigquery_types_are_converted_to_json_safe_values(self):
        self.assertEqual(queries._json_value(Decimal("12.25")), 12.25)
        self.assertEqual(queries._json_value(date(2024, 1, 2)), "2024-01-02")

    @patch.dict(os.environ, {"GCP_PROJECT_ID": "demo-project"})
    def test_dashboard_payload_uses_live_analytics_query_results(self):
        responses = [
            [{"total_waste": 12.5, "total_meals": 250, "waste_per_meal": 0.05}],
            [{"waste_date": "2024-01-01", "total_food_waste_kg": 12.5, "total_meals_served": 250,
              "average_food_waste_per_meal_kg": 0.05, "average_temperature_c": 20.0, "record_count": 1}],
            [{"waste_category": "Dairy", "total_food_waste_kg": 12.5, "percent_of_total_waste": 100.0}],
            [{"waste_month": "2024-01-01", "total_food_waste_kg": 12.5}],
        ]
        with patch.object(queries, "run_query", side_effect=responses) as run_query:
            payload = queries.dashboard_payload()
        self.assertEqual(payload["kpis"]["total_waste"], 12.5)
        self.assertEqual(payload["daily"][0]["total_meals_served"], 250)
        self.assertEqual(payload["categories"][0]["waste_category"], "Dairy")
        self.assertEqual(len(payload["monthly"]), 1)
        self.assertEqual(run_query.call_count, 4)


class FrontendTests(unittest.TestCase):
    def test_frontend_is_separate_and_uses_interactive_chart_library(self):
        frontend = ROOT / "frontend"
        self.assertTrue((frontend / "index.html").exists())
        self.assertTrue((frontend / "styles.css").exists())
        script = (frontend / "app.js").read_text(encoding="utf-8")
        html = (frontend / "index.html").read_text(encoding="utf-8")
        self.assertIn("chart.js", html.lower())
        self.assertIn("doughnut", script)
        self.assertIn("scatter", script)
        self.assertIn("/api/dashboard", script)

    def test_streamlit_frontend_source_was_removed(self):
        self.assertFalse((ROOT / "streamlit" / "app.py").exists())


if __name__ == "__main__":
    unittest.main()
