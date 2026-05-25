from __future__ import annotations

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from coingecko.config import CoinGeckoSettings, get_coingecko_settings


class CoinGeckoClient:
    def __init__(self, settings: CoinGeckoSettings | None = None) -> None:
        self.settings = settings or get_coingecko_settings()
        if not self.settings.api_key:
            raise RuntimeError(
                "COINGECKO_API_KEY esta vazia. Preencha o arquivo .env antes de rodar a DAG."
            )

        self.session = requests.Session()
        retry = Retry(
            total=5,
            connect=3,
            read=3,
            backoff_factor=2,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.headers.update(
            {
                "accept": "application/json",
                self.settings.api_key_header: self.settings.api_key,
            }
        )

    def _get(self, path: str, params: dict[str, Any]) -> Any:
        url = f"{self.settings.base_url}/{path.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def coins_markets(self, page: int, per_page: int) -> list[dict[str, Any]]:
        payload = self._get(
            "/coins/markets",
            {
                "vs_currency": self.settings.vs_currency,
                "order": "market_cap_desc",
                "per_page": per_page,
                "page": page,
                "sparkline": "false",
                "price_change_percentage": "24h,7d,30d",
            },
        )
        if not isinstance(payload, list):
            raise TypeError("Resposta inesperada de /coins/markets.")
        return payload

    def market_chart(self, coin_id: str) -> dict[str, list[list[float]]]:
        payload = self._get(
            f"/coins/{coin_id}/market_chart",
            {
                "vs_currency": self.settings.vs_currency,
                "days": self.settings.history_days,
                "interval": "daily",
            },
        )
        if not isinstance(payload, dict):
            raise TypeError(f"Resposta inesperada de /coins/{coin_id}/market_chart.")
        return payload
