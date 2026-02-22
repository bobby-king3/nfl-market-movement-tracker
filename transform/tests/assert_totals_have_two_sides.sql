-- Every total should have exactly two outcomes (Over and Under)
select event_id, captured_at, sportsbook
from {{ ref('stg_odds') }}
where market_type = 'totals'
group by event_id, captured_at, sportsbook
having count(distinct outcome) != 2
