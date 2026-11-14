FROM apache/airflow:2.10.4-python3.11
USER airflow
RUN mkdir -p /home/airflow/.dbt
COPY airflow/requirements.txt /requirements-airflow.txt
RUN pip install --no-cache-dir -r /requirements-airflow.txt --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.4/constraints-3.11.txt"
