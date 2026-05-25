from __future__ import annotations

import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from psycopg2.extras import Json, execute_values

from coingecko.client import CoinGeckoClient
from coingecko.config import get_coingecko_settings
from coingecko.db import ensure_raw_schema, warehouse_connection


def _as_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _as_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _from_epoch_ms(value: int | float) -> datetime:
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def load_markets_snapshot() -> dict[str, int | str]:
    settings = get_coingecko_settings()
    client = CoinGeckoClient(settings)

    per_page = min(settings.top_markets, 250)
    page_count = (settings.top_markets + per_page - 1) // per_page
    loaded_at = datetime.now(timezone.utc)
    run_id = uuid4()
    all_rows: list[dict[str, Any]] = []

    for page in range(1, page_count + 1):
        rows = client.coins_markets(page=page, per_page=per_page)
        remaining = settings.top_markets - len(all_rows)
        all_rows.extend(rows[:remaining])
        if page < page_count:
            time.sleep(settings.request_sleep_seconds)

    with warehouse_connection() as conn:
        ensure_raw_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into raw.coingecko_markets_run (
                    run_id,
                    loaded_at,
                    vs_currency,
                    requested_top_markets,
                    records_loaded,
                    payload
                )
                values (%s, %s, %s, %s, %s, %s)
                """,
                (
                    str(run_id),
                    loaded_at,
                    settings.vs_currency,
                    settings.top_markets,
                    len(all_rows),
                    Json({"coins": all_rows}),
                ),
            )

            execute_values(
                cur,
                """
                insert into raw.coingecko_markets (
                    run_id,
                    loaded_at,
                    vs_currency,
                    coin_id,
                    symbol,
                    name,
                    market_cap_rank,
                    current_price,
                    market_cap,
                    total_volume,
                    high_24h,
                    low_24h,
                    price_change_percentage_24h,
                    price_change_percentage_7d,
                    price_change_percentage_30d,
                    last_updated,
                    payload
                )
                values %s
                on conflict (run_id, coin_id) do nothing
                """,
                [
                    (
                        str(run_id),
                        loaded_at,
                        settings.vs_currency,
                        row.get("id"),
                        row.get("symbol"),
                        row.get("name"),
                        row.get("market_cap_rank"),
                        _as_decimal(row.get("current_price")),
                        _as_decimal(row.get("market_cap")),
                        _as_decimal(row.get("total_volume")),
                        _as_decimal(row.get("high_24h")),
                        _as_decimal(row.get("low_24h")),
                        _as_decimal(row.get("price_change_percentage_24h")),
                        _as_decimal(row.get("price_change_percentage_7d_in_currency")),
                        _as_decimal(row.get("price_change_percentage_30d_in_currency")),
                        _as_datetime(row.get("last_updated")),
                        Json(row),
                    )
                    for row in all_rows
                ],
            )

    return {"run_id": str(run_id), "records_loaded": len(all_rows)}


def _latest_market_coin_ids(source_run_id: UUID, limit: int) -> list[str]:
    with warehouse_connection() as conn:
        ensure_raw_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                select coin_id
                from raw.coingecko_markets
                where run_id = %s
                order by market_cap_rank nulls last, coin_id
                limit %s
                """,
                (str(source_run_id), limit),
            )
            return [row[0] for row in cur.fetchall()]


def load_market_chart_history(source_run_id: str) -> dict[str, int | str]:
    settings = get_coingecko_settings()
    client = CoinGeckoClient(settings)

    source_uuid = UUID(source_run_id)
    coin_ids = _latest_market_coin_ids(source_uuid, settings.history_top_coins)
    loaded_at = datetime.now(timezone.utc)
    run_id = uuid4()
    records: list[tuple[Any, ...]] = []

    for index, coin_id in enumerate(coin_ids):
        payload = client.market_chart(coin_id)
        prices = payload.get("prices", [])
        market_caps = {item[0]: item[1] for item in payload.get("market_caps", [])}
        volumes = {item[0]: item[1] for item in payload.get("total_volumes", [])}

        for observed_ms, price in prices:
            records.append(
                (
                    str(run_id),
                    loaded_at,
                    settings.vs_currency,
                    coin_id,
                    _from_epoch_ms(observed_ms),
                    _as_decimal(price),
                    _as_decimal(market_caps.get(observed_ms)),
                    _as_decimal(volumes.get(observed_ms)),
                    Json(
                        {
                            "price": [observed_ms, price],
                            "market_cap": [observed_ms, market_caps.get(observed_ms)],
                            "total_volume": [observed_ms, volumes.get(observed_ms)],
                        }
                    ),
                )
            )

        if index < len(coin_ids) - 1:
            time.sleep(settings.request_sleep_seconds)

    with warehouse_connection() as conn:
        ensure_raw_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into raw.coingecko_market_chart_run (
                    run_id,
                    source_markets_run_id,
                    loaded_at,
                    vs_currency,
                    history_days,
                    coins_requested,
                    records_loaded
                )
                values (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(run_id),
                    str(source_uuid),
                    loaded_at,
                    settings.vs_currency,
                    settings.history_days,
                    len(coin_ids),
                    len(records),
                ),
            )

            if records:
                execute_values(
                    cur,
                    """
                    insert into raw.coingecko_market_chart (
                        run_id,
                        loaded_at,
                        vs_currency,
                        coin_id,
                        observed_at,
                        price,
                        market_cap,
                        total_volume,
                        payload
                    )
                    values %s
                    on conflict (coin_id, observed_at, vs_currency) do update set
                        run_id = excluded.run_id,
                        loaded_at = excluded.loaded_at,
                        price = excluded.price,
                        market_cap = excluded.market_cap,
                        total_volume = excluded.total_volume,
                        payload = excluded.payload
                    """,
                    records,
                )

    return {"run_id": str(run_id), "records_loaded": len(records)}
