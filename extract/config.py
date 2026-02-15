import os
from dotenv import load_dotenv

load_dotenv()

odds_api_key = os.getenv("ODDS_API_KEY")
odds_api_base_url = "https://api.the-odds-api.com/v4"

sport_key = "americanfootball_nfl"

markets = ["spreads", "totals"]

#US listed sportsbooks
regions = "us"

odds_format = "american"

duckdb_path = os.path.join(os.path.dirname(__file__), "..", "data", "nfl_odds.duckdb")
