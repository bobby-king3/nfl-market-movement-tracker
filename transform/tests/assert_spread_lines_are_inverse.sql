select a.event_id, a.captured_at, a.sportsbook, a.line, b.line
from {{ ref('stg_odds') }} a
join {{ ref('stg_odds') }} b
    on a.event_id = b.event_id
    and a.captured_at = b.captured_at
    and a.sportsbook = b.sportsbook
    and a.market_type = b.market_type
    and a.outcome != b.outcome
where a.market_type = 'spreads'
    and a.line + b.line != 0
