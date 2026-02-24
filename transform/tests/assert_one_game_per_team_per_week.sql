-- A team should not appear in more than one game per nfl_week
with team_games as (
    select home_team as team, nfl_week, event_id
    from {{ ref('stg_odds') }}
    union
    select away_team as team, nfl_week, event_id
    from {{ ref('stg_odds') }}
)

select team, nfl_week, count(distinct event_id) as games
from team_games
group by team, nfl_week
having count(distinct event_id) > 1
