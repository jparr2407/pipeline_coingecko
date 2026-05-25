with daily as (
    select
        coin_id,
        vs_currency,
        observed_date,
        avg(price) as avg_price,
        avg(market_cap) as avg_market_cap,
        avg(total_volume) as avg_total_volume,
        max(loaded_at) as latest_loaded_at
    from {{ ref('stg_coingecko_market_chart') }}
    group by 1, 2, 3
),

with_changes as (
    select
        *,
        lag(avg_price) over (
            partition by coin_id, vs_currency
            order by observed_date
        ) as previous_avg_price
    from daily
)

select
    coin_id || '-' || observed_date::text || '-' || vs_currency as coin_market_daily_key,
    coin_id,
    vs_currency,
    observed_date,
    avg_price,
    avg_market_cap,
    avg_total_volume,
    previous_avg_price,
    case
        when previous_avg_price is null or previous_avg_price = 0 then null
        else ((avg_price - previous_avg_price) / previous_avg_price) * 100
    end as price_change_pct_day,
    latest_loaded_at
from with_changes
