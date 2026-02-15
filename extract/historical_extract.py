import json
import os
import time
from datetime import datetime, timedelta
import requests
from config import odds_api_key, odds_api_base_url, sport_key, markets, regions, odds_format

raw_data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

#2025 NFL Season
season_start = datetime(2025, 9, 4)
season_end = datetime(2026, 2, 9)

# 8am, 12pm, 4pm, 8pm CT = 14:00, 18:00, 22:00, 02:00 UTC
capture_hours_utc = [2, 14, 18, 22]

# Historical odds endpoint documentation can be found here: https://the-odds-api.com/liveapi/guides/v4/#get-historical-odds
def get_historical_odds(date_iso):
    url = f"{odds_api_base_url}/historical/sports/{sport_key}/odds"
    params = {
        "apiKey": odds_api_key,
        "regions": regions,
        "markets": ",".join(markets),
        "oddsFormat": odds_format,
        "dateFormat": "iso",
        "date": date_iso,
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    return response.json()

def generate_capture_timestamps(start, end):
    timestamps = []
    current_date = start

    while current_date <= end:
        for hour in capture_hours_utc:
            ts = current_date.replace(hour=hour, minute=0, second=0)
            timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))

        current_date += timedelta(days=1)

    return timestamps

def save_odds(data, timestamp_str):
    os.makedirs(raw_data_dir, exist_ok=True)
    clean_ts = timestamp_str.replace(":", "-").replace("T", "_").replace("Z", "")
    filename = f"nfl_odds_{clean_ts}.json"
    filepath = os.path.join(raw_data_dir, filename)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    return filepath

def odds_extract():
    all_timestamps = generate_capture_timestamps(season_start, season_end)
    print(f"Total timestamps to extract: {len(all_timestamps)}")

    skipped = 0
    extracted = 0
    failed = 0

    for i, timestamp in enumerate(all_timestamps):
        clean_ts = timestamp.replace(":", "-").replace("T", "_").replace("Z", "")
        filepath = os.path.join(raw_data_dir, f"nfl_odds_{clean_ts}.json")

        if os.path.exists(filepath):
            skipped += 1
            continue

        print(f"[{i+1}/{len(all_timestamps)}] Fetching {timestamp}...")

        try:
            data = get_historical_odds(timestamp)
        except requests.RequestException as e:
            print(f"Failed: {e}. Skipping.")
            failed += 1
            continue

        num_events = len(data.get("data", []))
        print(f"  Got {num_events} events")

        save_odds(data, timestamp)
        extracted += 1
        time.sleep(1)

    print(f"Extracted: {extracted}, Skipped: {skipped}, Failed: {failed}")

if __name__ == "__main__":
    odds_extract()
