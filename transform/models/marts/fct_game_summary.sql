with odds_with_open_close as (
    select
        *,
        first_value(line) over (
            partition by event_id, sportsbook, market_type, outcome
            order by captured_at
        ) as opening_line,
        last_value(line) over (
            partition by event_id, sportsbook, market_type, outcome
            order by captured_at
            rows between unbounded preceding and unbounded following
        ) as closing_line,
        first_value(price) over (
            partition by event_id, sportsbook, market_type, outcome
            order by captured_at
        ) as opening_price,
        last_value(price) over (
            partition by event_id, sportsbook, market_type, outcome
            order by captured_at
            rows between unbounded preceding and unbounded following
        ) as closing_price
    from {{ ref('stg_odds') }}
)

select
    event_id,
    home_team,
    away_team,
    game_start_time,
    sportsbook,
    market_type,
    outcome,
    opening_line,
    closing_line,
    closing_line - opening_line as total_line_movement,
    opening_price,
    closing_price,
    {{ implied_probability('opening_price') }} as opening_implied_prob,
    {{ implied_probability('closing_price') }} as closing_implied_prob,
    {{ implied_probability('closing_price') }} - {{ implied_probability('opening_price') }} as implied_prob_change,
    count(*) as capture_count,
    min(captured_at) as first_captured_at,
    max(captured_at) as last_captured_at
from odds_with_open_close
group by
    event_id,
    home_team,
    away_team,
    game_start_time,
    sportsbook,
    market_type,
    outcome,
    opening_line,
    closing_line,
    opening_price,
    closing_price
