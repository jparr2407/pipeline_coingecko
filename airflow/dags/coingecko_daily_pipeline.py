from __future__ import annotations

from datetime import timedelta

import pendulum
from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator


DEFAULT_ARGS = {
    "owner": "analytics",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


@dag(
    dag_id="coingecko_daily_pipeline",
    description="Carga CoinGecko raw e transformacoes dbt para Power BI.",
    schedule="@daily",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["coingecko", "dbt", "analytics-engineering"],
)
def coingecko_daily_pipeline():
    @task
    def load_markets() -> dict[str, int | str]:
        from coingecko.loaders import load_markets_snapshot

        return load_markets_snapshot()

    @task
    def load_history(markets_result: dict[str, int | str]) -> dict[str, int | str]:
        from coingecko.loaders import load_market_chart_history

        return load_market_chart_history(source_run_id=str(markets_result["run_id"]))

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command="cd /opt/airflow/dbt && /home/airflow/dbt-venv/bin/dbt build --target dev",
    )

    markets = load_markets()
    history = load_history(markets)
    history >> dbt_build


coingecko_daily_pipeline()
