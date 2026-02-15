# NFL Line Movement Tracker

Tracks how NFL betting lines move across sportsbooks over the course of the 2025-2026 season. Built as an ELT pipeline using Python, DuckDB, and dbt.

## Background

```
The Odds API → Python Extract → JSON Files → Python Load → DuckDB → dbt Transform
```

I pulled historical odds from [The Odds API](https://the-odds-api.com/) 4 times per day (8am, 12pm, 4pm, 8pm CT) for each sportsbook throughout the entirety of the 2025-2026 NFL season. The data is then loaded into DuckDB for dbt to model the data.

## Dataset

1.17M+ rows covering the full 2025-2026 NFL season, with spreads and totals from 32 sportsbooks across US, US2, and EU regions — including DraftKings, FanDuel, BetMGM, BetRivers, Pinnacle, and others. 636 total snapshots across the season.

## dbt models

**Staging**
- `stg_odds` — cleaned up raw odds with renamed columns, selected relevenant fields

**Marts**
- `fct_line_movements` — compares each capture to the previous offering to show when lines and prices moved
- `fct_game_summary` — one row per game/sportsbook/market with opening line, closing line, total movement, and implied probability conversion

**Tests**
- `not_null` and `accepted_values` on staging columns
- Custom tests validating that every spread has two sides and lines are properly inverse (+3 / -3)

## Instructions to Run Locally:

Download the DuckDB database from the [Releases page](https://github.com/bobby-king3/sports_betting_tracker/releases) and place it in the `data/` folder. No API key needed to run the dbt models.

```bash
git clone https://github.com/bobbyking/nfl-line-movement-tracker.git
cd nfl-line-movement-tracker

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Add your dbt profile to ~/.dbt/profiles.yml
# pointing to data/nfl_odds.duckdb

cd transform
dbt build
```

## Running the full pipeline

If you want to run the extract yourself, an [Odds API](https://the-odds-api.com/) account and API key is required

```bash
echo "ODDS_API_KEY=your_key_here" > .env

cd extract
python historical_extract.py

cd ../load
python load_to_duckdb.py

cd ../transform
dbt build
```

## dbt lineage

![dbt lineage graph](image.png)
