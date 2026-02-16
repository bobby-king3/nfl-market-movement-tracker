with odds as (
    select
        *,
        lag(line) over (
            partition by event_id, sportsbook, market_type, outcome
            order by captured_at
        ) as prev_line,
        lag(price) over (
            partition by event_id, sportsbook, market_type, outcome
            order by captured_at
        ) as prev_price
    from {{ ref('stg_odds') }}
)

select
    captured_at,
    game_start_time,
    nfl_week,
    event_id,
    home_team,
    away_team,
    sportsbook,
    market_type,
    outcome,
    line,
    prev_line,
    line - prev_line as line_change,
    price,
    prev_price,
    price - prev_price as price_change,
    {{ implied_probability('price') }} as implied_prob
from odds