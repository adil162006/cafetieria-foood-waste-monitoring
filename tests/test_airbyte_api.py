import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "airflow" / "dags"))
from airbyte_api import AirbyteAPI


class AirbyteApiTests(unittest.TestCase):
    @patch.dict(os.environ, {
        "AIRBYTE_API_URL": "http://airbyte.test/api/public/v1",
        "AIRBYTE_CONNECTION_ID": "connection-123",
        "AIRBYTE_API_CLIENT_ID": "client-id",
        "AIRBYTE_API_CLIENT_SECRET": "client-secret",
        "AIRBYTE_API_TOKEN": "",
    })
    @patch("airbyte_api.requests.post")
    def test_sync_fetches_fresh_token_and_triggers_job(self, post):
        token_response, job_response = MagicMock(), MagicMock()
        token_response.json.return_value = {"access_token": "short-lived-token"}
        job_response.json.return_value = {"jobId": 57}
        post.side_effect = [token_response, job_response]

        job_id = AirbyteAPI().trigger_sync()

        self.assertEqual(job_id, "57")
        self.assertEqual(post.call_args_list[0].args[0], "http://airbyte.test/api/public/v1/applications/token")
        self.assertEqual(post.call_args_list[1].args[0], "http://airbyte.test/api/public/v1/jobs")
        self.assertEqual(post.call_args_list[1].kwargs["json"], {"connectionId": "connection-123", "jobType": "sync"})
        self.assertEqual(post.call_args_list[1].kwargs["headers"]["Authorization"], "Bearer short-lived-token")

    @patch.dict(os.environ, {
        "AIRBYTE_API_URL": "http://airbyte.test/api/public/v1",
        "AIRBYTE_CONNECTION_ID": "connection-123",
        "AIRBYTE_API_TOKEN": "test-token",
        "AIRBYTE_API_CLIENT_ID": "",
        "AIRBYTE_API_CLIENT_SECRET": "",
    })
    @patch("airbyte_api.requests.get")
    def test_job_status_reads_airbyte_response(self, get):
        response = MagicMock()
        response.json.return_value = {"job": {"status": "running"}}
        get.return_value = response

        status = AirbyteAPI().job_status("57")

        self.assertEqual(status, "RUNNING")
        get.assert_called_once_with("http://airbyte.test/api/public/v1/jobs/57", headers=unittest.mock.ANY, timeout=30)


if __name__ == "__main__":
    unittest.main()
