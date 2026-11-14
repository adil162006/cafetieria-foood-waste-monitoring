import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("GCP_PROJECT_ID", "unit-test-project")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "streamlit"))
from queries.questions import execute_question, supported_questions


class QuestionTests(unittest.TestCase):
    def test_six_questions_are_fixed_to_analytics(self):
        questions = supported_questions()
        self.assertEqual(len(questions), 6)
        self.assertTrue(all("unit-test-project.food_waste_analytics" in q.sql for q in questions))
        self.assertTrue(all(";" not in q.sql for q in questions))

    def test_question_execution_uses_bigquery_client_and_returns_dataframe(self):
        expected = object()
        client = MagicMock()
        job = MagicMock()
        job.to_dataframe.return_value = expected
        client.query.return_value = job
        with patch("utils.bigquery_client.get_client", return_value=client):
            result = execute_question(supported_questions()[0])
        self.assertIs(result, expected)
        client.query.assert_called_once()
        self.assertIn("category_waste_summary", client.query.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
