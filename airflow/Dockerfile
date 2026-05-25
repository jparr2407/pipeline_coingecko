FROM apache/airflow:2.10.5-python3.11

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow
COPY requirements.txt /requirements.txt
COPY dbt-requirements.txt /dbt-requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt
RUN python -m venv /home/airflow/dbt-venv \
    && /home/airflow/dbt-venv/bin/pip install --no-cache-dir -r /dbt-requirements.txt
