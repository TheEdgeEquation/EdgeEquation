"""
engine/odds_fetcher.py
Fetches player-prop lines from The Odds API for all configured sports/markets.
"""
import requests
import logging
from datetime import datetime, timezone
from config.settings import (
    ODDS_API_KEY, ODDS_API_BASE, ODDS_API_REGIONS,
    ODDS_API_FORMAT, SPORT_MARKETS
)

logger = logging.getLogger(__name__)


def american_to_implied(odds: int) -> float:
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)


def fetch_props_for_sport(sport_key: str, market: str) -> list[dict]:
    url = f"{ODDS_API_BASE}/sports/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": ODDS_API_REGIONS,
        "markets": market,
        "oddsFormat": ODDS_API_FORMAT,
        "dateFormat": "iso",
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        games = resp.json()
        logger.info(f"[{sport_key}] {len(games)} games returned")
        return games
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 401:
            logger.error("Odds API: invalid API key")
        elif resp.status_code == 422:
            logger.warning(f"[{sport_key}/{market}] Market not available today — skipping")
        else:
            logger.error(f"[{sport_key}] HTTP error: {e}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"[{sport_key}] Request failed: {e}")
        return []


def parse_props(games: list[dict], sport_key: str) -> list[dict]:
    sport_cfg = SPORT_MARKETS[sport_key]
    props = []

    for game in games:
        home = game.get("home_team", "")
        away = game.get("away_team", "")
        commence = game.get("commence_time", "")

        for bookmaker in game.get("bookmakers", []):
            bk_name = bookmaker.get("title", "Unknown")
            for market in bookmaker.get("markets", []):
                for outcome in market.get("outcomes", []):
                    if outcome.get("name") != "Over":
                        continue

                    player = outcome.get("description", "Unknown Player")
                    line = outcome.get("point", 0.0)
                    over_odds = outcome.get("price", -110)

                    under_odds = -110
                    for other in market.get("outcomes", []):
                        if (other.get("name") == "Under"
                                and other.get("description") == player):
                            under_odds = other.get("price", -110)
                            break

                    implied = american_to_implied(over_odds)

                    props.append({
                        "player": player,
                        "team": home,
                        "opponent": away,
                        "sport": sport_key,
                        "sport_label": sport_cfg["label"],
                        "prop_label": sport_cfg["prop_label"],
                        "icon": sport_cfg["icon"],
                        "line": line,
                        "over_odds": over_odds,
                        "under_odds": under_odds,
                        "implied_prob": round(implied, 4),
                        "bookmaker": bk_name,
                        "commence_time": commence,
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                    })

    logger.info(f"[{sport_key}] {len(props)} over props parsed")
    return props


def fetch_all_props() -> list[dict]:
    if not ODDS_API_KEY:
        logger.error("ODDS_API_KEY not set — cannot fetch props")
        return []

    all_props = []
    for sport_key, cfg in SPORT_MARKETS.items():
        games = fetch_props_for_sport(sport_key, cfg["market"])
        parsed = parse_props(games, sport_key)
        all_props.extend(parsed)

    logger.info(f"Total props fetched: {len(all_props)}")
    return all_props
