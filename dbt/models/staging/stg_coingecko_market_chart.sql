with source as (
    select *
    from {{ source('raw', 'coingecko_market_chart') }}
)

select
    run_id,
    loaded_at,
    lower(coin_id) as coin_id, -- Minúsculo
    lower(vs_currency) as vs_currency, -- Minúsculo
    observed_at,
    observed_at::date as observed_date,
    price,
    market_cap,
    total_volume,
    payload
from source
where coin_id is not null -- Ignoramos aqueles dados sem coin_id definido
