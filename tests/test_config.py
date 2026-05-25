from coingecko.config import CoinGeckoSettings


def test_demo_settings_use_public_api_header() -> None:
    settings = CoinGeckoSettings(
        api_key="key",
        api_tier="demo",
        vs_currency="usd",
        top_markets=250,
        history_top_coins=20,
        history_days=90,
        request_sleep_seconds=1.5,
    )

    assert settings.base_url == "https://api.coingecko.com/api/v3"
    assert settings.api_key_header == "x-cg-demo-api-key"


def test_pro_settings_use_pro_api_header() -> None:
    settings = CoinGeckoSettings(
        api_key="key",
        api_tier="pro",
        vs_currency="usd",
        top_markets=250,
        history_top_coins=20,
        history_days=90,
        request_sleep_seconds=1.5,
    )

    assert settings.base_url == "https://pro-api.coingecko.com/api/v3"
    assert settings.api_key_header == "x-cg-pro-api-key"
