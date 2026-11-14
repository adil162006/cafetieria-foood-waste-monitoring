import unittest
from pathlib import Path

from scripts.inspect_dataset import EXPECTED, inspect


class DatasetInspectionTests(unittest.TestCase):
    def test_workspace_csv_matches_observed_schema_and_counts(self):
        result = inspect(Path(__file__).resolve().parents[1] / "train.csv")
        self.assertEqual(result["row_count"], 911)
        self.assertEqual(result["column_count"], 12)
        self.assertTrue(result["expected_columns_present"])
        self.assertEqual(set(result["columns"]), EXPECTED)
        self.assertEqual(result["exact_duplicate_rows"], 0)
        self.assertEqual(result["duplicate_IDs"], 0)
        self.assertEqual(result["invalid_dates"], 0)
        self.assertEqual(result["missing_or_nan"]["staff_experience"], 164)


if __name__ == "__main__":
    unittest.main()
