with source as (
    select *
    from {{ source('raw', 'coingecko_markets') }}
)

select
    run_id,
    loaded_at,
    lower(coin_id) as coin_id, -- Minúsculo
    upper(symbol) as symbol, -- Minúsculo
    name,
    lower(vs_currency) as vs_currency, -- Minúsculo
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
from source
where coin_id is not null -- Ignoramos aqueles dados sem coin_id definido
