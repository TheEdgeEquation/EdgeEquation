import requests
import logging
import os
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
 
 
def american_to_implied(odds):
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)
 
 
def get_nrfi_lines():
    if not ODDS_API_KEY:
        logger.warning("ODDS_API_KEY not set - using default NRFI implied probs")
        return {}
    try:
        url = ODDS_API_BASE + "/sports/baseball_mlb/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "pitcher_first_3_innings",
            "oddsFormat": "american",
        }
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 422:
            logger.warning("NRFI market not available from Odds API today")
            return {}
        resp.raise_for_status()
        games = resp.json()
        nrfi_lines = {}
        for game in games:
            home = game.get("home_team", "")
            away = game.get("away_team", "")
            game_key = away + "@" + home
            for bookmaker in game.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if "first" not in market.get("key", "").lower():
                        continue
                    for outcome in market.get("outcomes", []):
                        name = outcome.get("name", "").lower()
                        price = outcome.get("price", -135)
                        if "no" in name or "nrfi" in name:
                            implied = american_to_implied(price)
                            if game_key not in nrfi_lines:
                                nrfi_lines[game_key] = {}
                            nrfi_lines[game_key]["nrfi_implied"] = round(implied, 4)
                            nrfi_lines[game_key]["nrfi_odds"] = price
                        elif "yes" in name or "yrfi" in name:
                            implied = american_to_implied(price)
                            if game_key not in nrfi_lines:
                                nrfi_lines[game_key] = {}
                            nrfi_lines[game_key]["yrfi_implied"] = round(implied, 4)
                            nrfi_lines[game_key]["yrfi_odds"] = price
                        break
        logger.info("NRFI lines fetched for " + str(len(nrfi_lines)) + " games")
        return nrfi_lines
    except Exception as e:
        logger.error("NRFI lines fetch failed: " + str(e))
        return {}
 
 
def get_nrfi_implied_for_game(home_team, away_team, nrfi_lines=None):
    if nrfi_lines is None:
        nrfi_lines = get_nrfi_lines()
    game_key = away_team + "@" + home_team
    game_data = nrfi_lines.get(game_key, {})
    nrfi_implied = game_data.get("nrfi_implied", 0.574)
    yrfi_implied = game_data.get("yrfi_implied", 0.465)
    nrfi_odds = game_data.get("nrfi_odds", -135)
    yrfi_odds = game_data.get("yrfi_odds", 115)
    if game_data:
        logger.info("Live NRFI line for " + away_team + "@" + home_team + ": NRFI=" + str(nrfi_odds) + " YRFI=" + str(yrfi_odds))
    else:
        logger.info("No live NRFI line for " + away_team + "@" + home_team + " - using defaults")
    return nrfi_implied, yrfi_implied, nrfi_odds, yrfi_odds
