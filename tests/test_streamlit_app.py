import unittest
from pathlib import Path
from unittest.mock import patch
import os

from streamlit.testing.v1 import AppTest


class StreamlitAppTests(unittest.TestCase):
    def test_app_renders_without_cloud_credentials(self):
        app_path = Path(__file__).resolve().parents[1] / "streamlit" / "app.py"
        with patch.dict(os.environ, {"GCP_PROJECT_ID": ""}):
            app = AppTest.from_file(str(app_path)).run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("Cafeteria waste overview" in title.value for title in app.title))


if __name__ == "__main__":
    unittest.main()
