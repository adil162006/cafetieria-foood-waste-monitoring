"""Small client for Airbyte's supported public API."""
import os

import requests


class AirbyteAPI:
    def __init__(self) -> None:
        self.base_url = os.environ["AIRBYTE_API_URL"].rstrip("/")
        self.connection_id = os.environ["AIRBYTE_CONNECTION_ID"]

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        client_id = os.getenv("AIRBYTE_API_CLIENT_ID", "")
        client_secret = os.getenv("AIRBYTE_API_CLIENT_SECRET", "")
        if client_id and client_secret:
            response = requests.post(
                f"{self.base_url}/applications/token",
                headers=headers,
                json={"client_id": client_id, "client_secret": client_secret, "grant-type": "client_credentials"},
                timeout=30,
            )
            response.raise_for_status()
            token = response.json().get("access_token")
            if not token:
                raise RuntimeError("Airbyte token response did not include an access_token")
        else:
            token = os.getenv("AIRBYTE_API_TOKEN", "")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def trigger_sync(self) -> str:
        response = requests.post(
            f"{self.base_url}/jobs",
            headers=self._headers(),
            json={"connectionId": self.connection_id, "jobType": "sync"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        job_id = payload.get("jobId") or payload.get("id")
        if not job_id:
            raise RuntimeError("Airbyte sync request returned no jobId")
        return str(job_id)

    def job_status(self, job_id: str) -> str:
        response = requests.get(f"{self.base_url}/jobs/{job_id}", headers=self._headers(), timeout=30)
        response.raise_for_status()
        payload = response.json()
        return str(payload.get("job", payload).get("status", "")).upper()
