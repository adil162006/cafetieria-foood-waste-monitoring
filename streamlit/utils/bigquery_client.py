from google.cloud import bigquery
from google.oauth2 import service_account

from utils.config import setting


def get_client() -> bigquery.Client:
    project = setting("GCP_PROJECT_ID")
    if not project:
        raise RuntimeError("GCP_PROJECT_ID is missing. Configure it in the workspace .env file.")
    key_file = setting("GOOGLE_APPLICATION_CREDENTIALS")
    credentials = service_account.Credentials.from_service_account_file(key_file) if key_file else None
    return bigquery.Client(project=project, credentials=credentials, location=setting("BIGQUERY_LOCATION", "US"))


def query(sql: str, parameters: list | None = None):
    config = bigquery.QueryJobConfig(query_parameters=parameters or [])
    return get_client().query(sql, job_config=config).to_dataframe()
