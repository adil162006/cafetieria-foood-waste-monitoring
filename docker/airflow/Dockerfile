FROM apache/airflow:2.10.4-python3.11
USER airflow
RUN mkdir -p /home/airflow/.dbt
COPY airflow/requirements.txt /requirements-airflow.txt
RUN python -m venv /home/airflow/dbt-venv \
    && /home/airflow/dbt-venv/bin/pip install --no-cache-dir -r /requirements-airflow.txt
ENV PATH="/home/airflow/dbt-venv/bin:${PATH}"
