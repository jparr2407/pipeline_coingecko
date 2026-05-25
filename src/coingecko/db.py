from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg2
from psycopg2.extensions import connection

from coingecko.config import WarehouseSettings, get_warehouse_settings


@contextmanager
def warehouse_connection(settings: WarehouseSettings | None = None) -> Iterator[connection]:
    cfg = settings or get_warehouse_settings()
    conn = psycopg2.connect(
        host=cfg.host,
        port=cfg.port,
        dbname=cfg.database,
        user=cfg.user,
        password=cfg.password,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ensure_raw_schema(conn: connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            create schema if not exists raw;

            create table if not exists raw.coingecko_markets_run (
                run_id uuid primary key,
                loaded_at timestamptz not null,
                vs_currency text not null,
                requested_top_markets integer not null,
                records_loaded integer not null,
                payload jsonb not null
            );

            create table if not exists raw.coingecko_markets (
                run_id uuid not null references raw.coingecko_markets_run(run_id),
                loaded_at timestamptz not null,
                vs_currency text not null,
                coin_id text not null,
                symbol text,
                name text,
                market_cap_rank integer,
                current_price numeric,
                market_cap numeric,
                total_volume numeric,
                high_24h numeric,
                low_24h numeric,
                price_change_percentage_24h numeric,
                price_change_percentage_7d numeric,
                price_change_percentage_30d numeric,
                last_updated timestamptz,
                payload jsonb not null,
                primary key (run_id, coin_id)
            );

            create table if not exists raw.coingecko_market_chart_run (
                run_id uuid primary key,
                source_markets_run_id uuid references raw.coingecko_markets_run(run_id),
                loaded_at timestamptz not null,
                vs_currency text not null,
                history_days integer not null,
                coins_requested integer not null,
                records_loaded integer not null
            );

            create table if not exists raw.coingecko_market_chart (
                run_id uuid not null references raw.coingecko_market_chart_run(run_id),
                loaded_at timestamptz not null,
                vs_currency text not null,
                coin_id text not null,
                observed_at timestamptz not null,
                price numeric,
                market_cap numeric,
                total_volume numeric,
                payload jsonb not null,
                primary key (coin_id, observed_at, vs_currency)
            );
            """
        )
