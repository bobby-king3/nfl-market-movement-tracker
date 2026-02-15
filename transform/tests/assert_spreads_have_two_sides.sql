select event_id, captured_at, sportsbook
from {{ ref('stg_odds') }}
where market_type = 'spreads'
group by event_id, captured_at, sportsbook
having count(distinct outcome) != 2
