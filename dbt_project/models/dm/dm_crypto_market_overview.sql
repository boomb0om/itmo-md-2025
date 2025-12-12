{{
    config(
        materialized='table',
        unique_key='symbol'
    )
}}

with latest_prices as (
    select
        symbol,
        trade_date,
        daily_close as current_price,
        daily_volume,
        daily_trades_count,
        price_change_pct as daily_change_pct,

        -- Calculate moving averages using window functions
        avg(daily_close) over (
            partition by symbol
            order by trade_date
            rows between 6 preceding and current row
        ) as ma_7d,

        avg(daily_close) over (
            partition by symbol
            order by trade_date
            rows between 29 preceding and current row
        ) as ma_30d,

        -- Volatility metric (standard deviation)
        stddev(price_change_pct) over (
            partition by symbol
            order by trade_date
            rows between 6 preceding and current row
        ) as volatility_7d,

        row_number() over (partition by symbol order by trade_date desc) as rn

    from {{ ref('ods_binance_daily_agg') }}
),

price_stats as (
    select
        symbol,
        trade_date as last_update_date,
        current_price,
        daily_volume as volume_24h,
        daily_trades_count as trades_24h,
        daily_change_pct,
        round(ma_7d::numeric, 2) as ma_7d,
        round(ma_30d::numeric, 2) as ma_30d,
        round(volatility_7d::numeric, 2) as volatility_7d,

        -- Trend indicator
        case
            when current_price > ma_7d and ma_7d > ma_30d then 'uptrend'
            when current_price < ma_7d and ma_7d < ma_30d then 'downtrend'
            else 'sideways'
        end as trend_indicator

    from latest_prices
    where rn = 1
)

select
    symbol,
    last_update_date,
    current_price,
    volume_24h,
    trades_24h,
    daily_change_pct,
    ma_7d,
    ma_30d,
    volatility_7d,
    trend_indicator,
    current_timestamp as processed_dttm

from price_stats
