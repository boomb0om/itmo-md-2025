{{
    config(
        materialized='incremental',
        incremental_strategy='delete+insert',
        unique_key='binance_id'
    )
}}

with source_data as (
    select
        id,
        process_at,
        data
    from {{ source('raw_data', 'raw_binance_data') }}

    {% if is_incremental() %}
    where process_at > (select max(process_at) from {{ this }})
    {% endif %}
)

select
    -- Primary key
    id as binance_id,

    -- Metadata
    process_at,
    current_timestamp as processed_dttm,

    -- Binance candle data
    (data->>'symbol')::varchar as symbol,
    (data->>'interval')::varchar as interval,
    (data->>'open_time')::timestamp as open_time,
    (data->>'close_time')::timestamp as close_time,

    -- OHLCV data
    (data->>'open')::decimal(20,8) as open_price,
    (data->>'high')::decimal(20,8) as high_price,
    (data->>'low')::decimal(20,8) as low_price,
    (data->>'close')::decimal(20,8) as close_price,
    (data->>'volume')::decimal(20,8) as volume,

    -- Additional trading metrics
    (data->>'quote_asset_volume')::decimal(20,8) as quote_asset_volume,
    (data->>'number_of_trades')::integer as number_of_trades,
    (data->>'taker_buy_base_asset_volume')::decimal(20,8) as taker_buy_base_asset_volume,
    (data->>'taker_buy_quote_asset_volume')::decimal(20,8) as taker_buy_quote_asset_volume,

    -- Source timestamp
    (data->>'created_at')::timestamp as created_at

from source_data
