from __future__ import annotations

import os
from dataclasses import dataclass


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value not in (None, "") else default


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value not in (None, "") else default


@dataclass(frozen=True)
class CoinGeckoSettings:
    api_key: str
    api_tier: str
    vs_currency: str
    top_markets: int
    history_top_coins: int
    history_days: int
    request_sleep_seconds: float

    @property
    def base_url(self) -> str:
        if self.api_tier == "pro":
            return "https://pro-api.coingecko.com/api/v3"
        return "https://api.coingecko.com/api/v3"

    @property
    def api_key_header(self) -> str:
        if self.api_tier == "pro":
            return "x-cg-pro-api-key"
        return "x-cg-demo-api-key"


@dataclass(frozen=True)
class WarehouseSettings:
    host: str
    port: int
    database: str
    user: str
    password: str


def get_coingecko_settings() -> CoinGeckoSettings:
    tier = os.getenv("COINGECKO_API_TIER", "demo").lower().strip()
    if tier not in {"demo", "pro"}:
        raise ValueError("COINGECKO_API_TIER deve ser 'demo' ou 'pro'.")

    return CoinGeckoSettings(
        api_key=os.getenv("COINGECKO_API_KEY", "").strip(),
        api_tier=tier,
        vs_currency=os.getenv("COINGECKO_VS_CURRENCY", "usd").lower().strip(),
        top_markets=_int_env("COINGECKO_TOP_MARKETS", 250),
        history_top_coins=_int_env("COINGECKO_HISTORY_TOP_COINS", 20),
        history_days=_int_env("COINGECKO_HISTORY_DAYS", 90),
        request_sleep_seconds=_float_env("COINGECKO_REQUEST_SLEEP_SECONDS", 1.5),
    )


def get_warehouse_settings() -> WarehouseSettings:
    return WarehouseSettings(
        host=os.getenv("WAREHOUSE_HOST", "localhost"),
        port=_int_env("WAREHOUSE_PORT", 5432),
        database=os.getenv("WAREHOUSE_DB", "crypto_warehouse"),
        user=os.getenv("WAREHOUSE_USER", "analytics"),
        password=os.getenv("WAREHOUSE_PASSWORD", "analytics"),
    )
