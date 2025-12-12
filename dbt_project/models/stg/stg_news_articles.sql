{{
    config(
        materialized='incremental',
        incremental_strategy='delete+insert',
        unique_key='news_id'
    )
}}

with source_data as (
    select
        id,
        process_at,
        data
    from {{ source('raw_data', 'raw_news_data') }}

    {% if is_incremental() %}
    where process_at > (select max(process_at) from {{ this }})
    {% endif %}
)

select
    -- Primary key
    id as news_id,

    -- Metadata
    process_at,
    current_timestamp as processed_dttm,

    -- News article data
    (data->>'guid')::varchar as guid,
    (data->>'source')::varchar as source,
    (data->>'title')::varchar as title,
    (data->>'link')::varchar as link,
    (data->>'description')::text as description,
    (data->>'pub_date')::timestamp as pub_date,

    -- Categories as JSON array
    (data->'categories')::jsonb as categories,

    -- Source timestamp
    (data->>'created_at')::timestamp as created_at

from source_data
