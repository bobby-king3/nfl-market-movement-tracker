-- Implied probability for any single outcome must be between 0 and 1
select event_id, captured_at, sportsbook, outcome, implied_prob
from {{ ref('fct_line_movements') }}
where implied_prob is null
   or implied_prob <= 0
   or implied_prob >= 1
