import requests
import logging
import os
from config.settings import ODDS_API_KEY, ODDS_API_BASE, SPORT_MARKETS
 
logger = logging.getLogger(__name__)
 
 
def american_to_implied(odds):
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)
 
 
def fetch_all_props():
    logger.info("Fetching props from DraftKings (primary)...")
    try:
        from engine.dk_fetcher import fetch_all_dk_props
        dk_props = fetch_all_dk_props()
        if dk_props:
            logger.info("DraftKings returned " + str(len(dk_props)) + " props")
            return dk_props
        else:
            logger.warning("DraftKings returned no props - trying Odds API fallback...")
    except Exception as e:
        logger.error("DraftKings fetch failed: " + str(e) + " - trying Odds API fallback...")
 
    logger.info("Fetching props from Odds API (fallback)...")
    return fetch_odds_api_props()
 
 
def fetch_odds_api_props():
    if not ODDS_API_KEY:
        logger.warning("ODDS_API_KEY not set")
        return []
 
    all_props = []
    for sport, config in SPORT_MARKETS.items():
        market = config["market"]
        label = config["label"]
        prop_label = config["prop_label"]
        icon = config.get("icon", "")
        try:
            url = ODDS_API_BASE + "/sports/" + sport + "/odds"
            params = {
                "apiKey": ODDS_API_KEY,
                "regions": "us",
                "markets": market,
                "oddsFormat": "american",
            }
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code == 422:
                logger.warning("[" + sport + "/" + market + "] Market not available today")
                continue
            resp.raise_for_status()
            games = resp.json()
            count = 0
            for game in games:
                home = game.get("home_team", "")
                away = game.get("away_team", "")
                commence = game.get("commence_time", "")
                for bookmaker in game.get("bookmakers", [])[:1]:
                    for mkt in bookmaker.get("markets", []):
                        if mkt.get("key") != market:
                            continue
                        outcomes = mkt.get("outcomes", [])
                        players = {}
                        for outcome in outcomes:
                            name = outcome.get("name", "")
                            desc = outcome.get("description", "")
                            price = outcome.get("price", -110)
                            point = outcome.get("point", None)
                            player = desc if desc else name
                            if player not in players:
                                players[player] = {}
                            if "Over" in name:
                                players[player]["over_odds"] = price
                                if point is not None:
                                    players[player]["line"] = point
                            elif "Under" in name:
                                players[player]["under_odds"] = price
                        for player, data in players.items():
                            if "over_odds" not in data or "line" not in data:
                                continue
                            implied = american_to_implied(data["over_odds"])
                            all_props.append({
                                "player": player,
                                "team": home,
                                "opponent": away,
                                "sport": sport,
                                "sport_label": label,
                                "prop_label": prop_label,
                                "icon": icon,
                                "line": data["line"],
                                "over_odds": data["over_odds"],
                                "under_odds": data.get("under_odds", -110),
                                "implied_prob": round(implied, 4),
                                "commence_time": commence,
                                "source": "odds_api",
                            })
                            count += 1
            logger.info("[" + sport + "] " + str(count) + " over props parsed")
        except Exception as e:
            logger.error("[" + sport + "] fetch failed: " + str(e))
 
    return all_props
