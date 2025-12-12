{{
    config(
        materialized='incremental',
        incremental_strategy='merge',
        unique_key=['symbol', 'trade_date']
    )
}}

with daily_klines as (
    select
        symbol,
        date(open_time) as trade_date,

        -- Daily OHLC using window functions
        first_value(open_price) over (
            partition by symbol, date(open_time)
            order by open_time
            rows between unbounded preceding and unbounded following
        ) as daily_open,

        max(high_price) as daily_high,
        min(low_price) as daily_low,

        last_value(close_price) over (
            partition by symbol, date(open_time)
            order by open_time
            rows between unbounded preceding and unbounded following
        ) as daily_close,

        sum(volume) as daily_volume,
        sum(quote_asset_volume) as daily_quote_volume,
        sum(number_of_trades) as daily_trades_count,

        count(*) as candles_count,
        current_timestamp as processed_dttm

    from {{ ref('stg_binance_klines') }}

    {% if is_incremental() %}
    where date(open_time) >= (
        select max(trade_date) - interval '1 day'
        from {{ this }}
    )
    {% endif %}

    group by symbol, date(open_time)
)

select distinct
    symbol,
    trade_date,
    daily_open,
    daily_high,
    daily_low,
    daily_close,
    daily_volume,
    daily_quote_volume,
    daily_trades_count,
    candles_count,

    -- Price change metrics
    round((daily_close - daily_open) / daily_open * 100, 2) as price_change_pct,
    round(daily_close - daily_open, 8) as price_change_abs,

    processed_dttm

from daily_klines
