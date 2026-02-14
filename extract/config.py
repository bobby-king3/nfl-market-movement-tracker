import os
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"

SPORT_KEY = "americanfootball_nfl"

MARKETS = ["spreads", "totals"]

# US sportsbooks
REGIONS = "us"

ODDS_FORMAT = "american"
