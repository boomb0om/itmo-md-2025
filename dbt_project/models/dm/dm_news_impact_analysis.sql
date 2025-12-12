{{
    config(
        materialized='table'
    )
}}

with daily_news_sentiment as (
    select
        pub_date_only as news_date,
        sentiment,
        count(*) as news_count,
        avg(title_length) as avg_title_length,
        sum(case when sentiment = 'positive' then 1 else 0 end) as positive_count,
        sum(case when sentiment = 'negative' then 1 else 0 end) as negative_count,
        sum(case when sentiment = 'neutral' then 1 else 0 end) as neutral_count

    from {{ ref('ods_news_enriched') }}
    group by pub_date_only, sentiment
),

sentiment_aggregated as (
    select
        news_date,
        sum(news_count) as total_news_count,
        sum(positive_count) as total_positive,
        sum(negative_count) as total_negative,
        sum(neutral_count) as total_neutral,

        -- Sentiment score: positive minus negative
        sum(positive_count) - sum(negative_count) as sentiment_score,

        -- Sentiment ratio
        case
            when sum(news_count) > 0
            then round((sum(positive_count)::decimal / sum(news_count)::decimal) * 100, 2)
            else 0
        end as positive_ratio

    from daily_news_sentiment
    group by news_date
),

price_changes as (
    select
        trade_date,
        symbol,
        price_change_pct,
        daily_volume

    from {{ ref('ods_binance_daily_agg') }}
)

select
    coalesce(s.news_date, p.trade_date) as analysis_date,
    p.symbol,

    -- News metrics
    coalesce(s.total_news_count, 0) as news_count,
    coalesce(s.total_positive, 0) as positive_news,
    coalesce(s.total_negative, 0) as negative_news,
    coalesce(s.sentiment_score, 0) as sentiment_score,
    coalesce(s.positive_ratio, 0) as positive_ratio,

    -- Price metrics
    p.price_change_pct,
    p.daily_volume,

    -- Impact indicator (correlation between sentiment and price change)
    case
        when s.sentiment_score > 0 and p.price_change_pct > 0 then 'positive_correlation'
        when s.sentiment_score < 0 and p.price_change_pct < 0 then 'positive_correlation'
        when s.sentiment_score > 0 and p.price_change_pct < 0 then 'negative_correlation'
        when s.sentiment_score < 0 and p.price_change_pct > 0 then 'negative_correlation'
        else 'no_correlation'
    end as sentiment_price_correlation,

    current_timestamp as processed_dttm

from sentiment_aggregated s
full outer join price_changes p
    on s.news_date = p.trade_date

where coalesce(s.news_date, p.trade_date) is not null
