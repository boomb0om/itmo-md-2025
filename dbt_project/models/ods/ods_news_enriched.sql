{{
    config(
        materialized='incremental',
        incremental_strategy='merge',
        unique_key='news_id'
    )
}}

with news_with_attributes as (
    select
        news_id,
        guid,
        source,
        title,
        link,
        description,
        pub_date,
        date(pub_date) as pub_date_only,
        categories,
        created_at,
        process_at,

        -- Extract hour for time analysis
        extract(hour from pub_date) as pub_hour,
        extract(dow from pub_date) as pub_day_of_week,

        -- Text analysis
        length(title) as title_length,
        length(description) as description_length,

        -- Category analysis
        jsonb_array_length(categories) as categories_count,

        -- Sentiment indicators (simple keyword matching)
        case
            when lower(title) similar to '%(bull|bullish|surge|rally|gain|up|rise|positive)%' then 'positive'
            when lower(title) similar to '%(bear|bearish|crash|fall|drop|down|decline|negative)%' then 'negative'
            else 'neutral'
        end as sentiment,

        current_timestamp as processed_dttm

    from {{ ref('stg_news_articles') }}

    {% if is_incremental() %}
    where process_at > (select max(process_at) from {{ this }})
    {% endif %}
)

select * from news_with_attributes
