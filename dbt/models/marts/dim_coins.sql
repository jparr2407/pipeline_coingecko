with ranked as (
    select
        coin_id,
        symbol,
        name,
        market_cap_rank,
        loaded_at,
        row_number() over (
            partition by coin_id
            order by loaded_at desc, market_cap_rank nulls last
        ) as row_num
    from {{ ref('stg_coingecko_markets') }}
)

select
    coin_id,
    symbol,
    name,
    market_cap_rank as latest_market_cap_rank,
    loaded_at as latest_loaded_at
from ranked
where row_num = 1
