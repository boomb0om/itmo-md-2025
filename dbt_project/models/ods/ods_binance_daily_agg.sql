{{
    config(
        materialized='incremental',
        incremental_strategy='delete+insert',
        unique_key=['symbol', 'trade_date']
    )
}}

with daily_aggregates as (
    select
        symbol,
        date(open_time) as trade_date,
        max(high_price) as daily_high,
        min(low_price) as daily_low,
        sum(volume) as daily_volume,
        sum(quote_asset_volume) as daily_quote_volume,
        sum(number_of_trades) as daily_trades_count,
        count(*) as candles_count,
        min(open_time) as first_candle_time,
        max(open_time) as last_candle_time

    from {{ ref('stg_binance_klines') }}

    {% if is_incremental() %}
    where date(open_time) >= (
        select max(trade_date) - interval '1 day'
        from {{ this }}
    )
    {% endif %}

    group by symbol, date(open_time)
),

daily_klines as (
    select
        agg.*,
        first_kline.open_price as daily_open,
        last_kline.close_price as daily_close,
        current_timestamp as processed_dttm
    from daily_aggregates agg
    left join {{ ref('stg_binance_klines') }} first_kline
        on agg.symbol = first_kline.symbol
        and agg.first_candle_time = first_kline.open_time
    left join {{ ref('stg_binance_klines') }} last_kline
        on agg.symbol = last_kline.symbol
        and agg.last_candle_time = last_kline.open_time
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
