import requests
import os

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
BASE = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

def get_batter_prop_lines(league):
    if league != "MLB":
        return {}

    if not ODDS_API_KEY:
        return {}

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "player_props",
        "oddsFormat": "american",
    }

    try:
        resp = requests.get(BASE, params=params, timeout=10)
        data = resp.json()
    except Exception:
        return {}

    lines = {}

    for game in data:
        for bm in game.get("bookmakers", []):
            for market in bm.get("markets", []):
                key = market.get("key", "")
                outcomes = market.get("outcomes", [])

                # Map Odds API keys to our prop labels
                if key == "player_hits":
                    prop_label = "HITS"
                elif key == "player_total_bases":
                    prop_label = "TOTAL_BASES"
                elif key == "player_home_runs":
                    prop_label = "HOME_RUNS"
                elif key == "player_rbi":
                    prop_label = "RBI"
                elif key == "player_runs":
                    prop_label = "RUNS"
                else:
                    continue

                for o in outcomes:
                    player = o.get("description", "")
                    line = o.get("point", None)
                    odds = o.get("price", None)

                    if player and line is not None and odds is not None:
                        lines[(player, prop_label)] = {
                            "line": line,
                            "over_odds": odds,
                            "under_odds": -odds,  # safe fallback
                            "implied_prob": abs(odds) / (abs(odds) + 100),
                        }

    return lines
