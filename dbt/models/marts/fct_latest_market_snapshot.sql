with ranked as (
    select
        *,
        row_number() over (
            partition by coin_id, vs_currency
            order by loaded_at desc, market_cap_rank nulls last
        ) as row_num
    from {{ ref('stg_coingecko_markets') }}
)

select
    coin_id || '-' || vs_currency as market_snapshot_key,
    coin_id,
    vs_currency,
    loaded_at,
    market_cap_rank,
    current_price,
    market_cap,
    total_volume,
    high_24h,
    low_24h,
    price_change_percentage_24h,
    price_change_percentage_7d,
    price_change_percentage_30d,
    last_updated
from ranked
where row_num = 1
