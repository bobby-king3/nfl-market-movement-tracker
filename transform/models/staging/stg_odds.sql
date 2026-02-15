with raw_odds as (
    select *
    from {{ source('raw', 'raw_odds') }}
)

select
    captured_at,
    commence_time as game_start_time,
    least(
        floor((commence_time::date - date '2025-09-03') / 7) + 1,
        22
    )::int as nfl_week,
    event_id,
    home_team,
    away_team,
    bookmaker_key as sportsbook,
    bookmaker_last_update as sportsbook_updated_at,
    market_key as market_type,
    outcome_name as outcome,
    outcome_price as price,
    outcome_point as line
from raw_odds
where captured_at < commence_time