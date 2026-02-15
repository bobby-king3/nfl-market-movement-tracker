import json
import os
import glob
import duckdb

raw_data = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
duckdb_path = os.path.join(os.path.dirname(__file__), "..", "data", "nfl_odds.duckdb")

def flatten_odds_file(filepath):
    with open(filepath) as f:
        data = json.load(f)

    ts = data["timestamp"]
    rows = []
    for e in data["data"]:
        for b in e["bookmakers"]:
            for m in b["markets"]:
                for o in m["outcomes"]:
                    rows.append((
                        ts, e["id"], e["sport_key"], e["commence_time"],
                        e["home_team"], e["away_team"], b["key"], b["title"],
                        b["last_update"], m["key"], o["name"], o["price"],
                        o.get("point"),
                    ))
    return rows

def load_all_odds():
    os.makedirs(os.path.dirname(duckdb_path), exist_ok=True)
    conn = duckdb.connect(duckdb_path)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw_odds (
            captured_at          TIMESTAMP,
            event_id             VARCHAR,
            sport_key            VARCHAR,
            commence_time        TIMESTAMP,
            home_team            VARCHAR,
            away_team            VARCHAR,
            bookmaker_key        VARCHAR,
            bookmaker_title      VARCHAR,
            bookmaker_last_update TIMESTAMP,
            market_key           VARCHAR,
            outcome_name         VARCHAR,
            outcome_price        DOUBLE,
            outcome_point        DOUBLE,
            loaded_at            TIMESTAMP DEFAULT current_timestamp
        )
    """)

    existing = conn.execute("SELECT COUNT(*) FROM raw_odds").fetchone()[0]
    if existing > 0:
        print(f"Already loaded ({existing:,} rows). Skipping.")
        conn.close()
        return

    files = sorted(glob.glob(os.path.join(raw_data, "nfl_odds_*.json")))
    if not files:
        print("No odds files found. Run the extraction first.")
        conn.close()
        return

    rows = [r for f in files for r in flatten_odds_file(f)]
    conn.executemany(
        """INSERT INTO raw_odds (
            captured_at, event_id, sport_key, commence_time,
            home_team, away_team, bookmaker_key, bookmaker_title,
            bookmaker_last_update, market_key, outcome_name,
            outcome_price, outcome_point
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )

    conn.close()
    print(f"Loaded {len(rows):,} rows from {len(files)} files into {duckdb_path}")


if __name__ == "__main__":
    load_all_odds()
