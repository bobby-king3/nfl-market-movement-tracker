-- Confirm data is only for prematch wagers and not live 
select *
from {{ ref('stg_odds') }}
where captured_at >= game_start_time
