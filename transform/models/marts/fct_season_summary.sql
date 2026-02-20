with pinnacle as (
    select *
    from {{ ref('fct_game_summary') }}
    where sportsbook = 'pinnacle'
)

select
    event_id,
    home_team,
    away_team,
    game_start_time,
    nfl_week,
    market_type,
    outcome,
    opening_line,
    closing_line,
    total_line_movement,
    abs(total_line_movement) as abs_line_movement,
    opening_price,
    closing_price,
    opening_implied_prob_pct,
    closing_implied_prob_pct,
    implied_prob_pct_change,
    capture_count,
    first_captured_at,
    datediff('day', first_captured_at, game_start_time) as days_of_data
from pinnacle
