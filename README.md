# NFL Line Movement Tracker

Tracks how NFL betting lines move across US sportsbooks over the course of the 2025 season. Built as an ELT pipeline using Python, DuckDB, and dbt.

## How it works

```
The Odds API → Python Extract → JSON Files → Python Load → DuckDB → dbt Transform
```

I pull historical odds from [The Odds API](https://the-odds-api.com/) 4 times per day (8am, 12pm, 4pm, 8pm CT), flatten the nested JSON into DuckDB, then use dbt to model the data.

## Dataset

469K+ rows covering the full 2025 NFL season (Sept 4 - Feb 9), with spreads and totals from 10+ US sportsbooks including DraftKings, FanDuel, BetMGM, BetRivers, and others. 636 total snapshots across the season.

## dbt models

**Staging**
- `stg_odds` — cleaned up raw odds with renamed columns, drops load artifacts

**Marts**
- `fct_line_movements` — compares each capture to the previous offering to show when lines and prices moved
- `fct_game_summary` — one row per game/sportsbook/market with opening line, closing line, and total movement

**Tests**
- `not_null` and `accepted_values` on staging columns
- Custom tests validating that every spread has two sides and lines are properly inverse (+3 / -3)

## Instructions to Run Locally:

The DuckDB database with the full season is included in the repo, so you do not need an API key to run the dbt models.

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
