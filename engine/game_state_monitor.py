"""
Edge Equation — Game State Monitor
Polls game status from The Odds API.
Exposes: slate_live(), slate_final(), games_scheduled()
Used by Logic Layer to gate results and cheeky posts.
"""
 
import os
import logging
import requests
from datetime import datetime, timezone
 
logger = logging.getLogger(__name__)
 
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
 
# Sport keys for each league
SPORT_KEYS = {
    "MLB":   "baseball_mlb",
    "NBA":   "basketball_nba",
    "NHL":   "icehockey_nhl",
    "NFL":   "americanfootball_nfl",
    "WNBA":  "basketball_wnba",
    "NCAAF": "americanfootball_ncaaf",
    "NCAAB": "basketball_ncaab",
    "KBO":   "baseball_kbo",
    "NPB":   "baseball_npb",
    "EPL":   "soccer_epl",
    "UCL":   "soccer_uefa_champs_league",
}
 
# EE sports (daytime)
EE_SPORTS = ["MLB", "NBA", "NHL", "NFL", "WNBA", "NCAAF", "NCAAB"]
 
# CBC sports (overnight)
CBC_SPORTS = ["KBO", "NPB", "EPL", "UCL"]
 
 
def _get_scores(sport_key: str) -> list:
    """Fetch scores/status from Odds API for a sport."""
    if not ODDS_API_KEY:
        logger.warning("ODDS_API_KEY not set")
        return []
    try:
        url = f"{ODDS_API_BASE}/sports/{sport_key}/scores"
        params = {
            "apiKey": ODDS_API_KEY,
            "daysFrom": 1,
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 422:
            # Sport not in season
            return []
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Score fetch failed for {sport_key}: {e}")
        return []
 
 
def _classify_games(games: list) -> dict:
    """Classify games into scheduled/live/final."""
    result = {"scheduled": [], "live": [], "final": []}
    for g in games:
        completed = g.get("completed", False)
        scores = g.get("scores")
        if completed:
            result["final"].append(g)
        elif scores:
            result["live"].append(g)
        else:
            result["scheduled"].append(g)
    return result
 
 
def get_slate_status(brand: str = "EE") -> dict:
    """
    Get combined slate status for EE or CBC.
    Returns:
        {
            "any_live": bool,
            "all_final": bool,
            "any_scheduled": bool,
            "sports_active": list,
            "sports_live": list,
            "sports_final": list,
        }
    """
    sports = EE_SPORTS if brand == "EE" else CBC_SPORTS
    any_live = False
    all_final = True
    any_scheduled = False
    sports_active = []
    sports_live = []
    sports_final = []
 
    for sport in sports:
        sport_key = SPORT_KEYS.get(sport)
        if not sport_key:
            continue
 
        games = _get_scores(sport_key)
        if not games:
            continue
 
        classified = _classify_games(games)
        has_games = bool(classified["scheduled"] or classified["live"] or classified["final"])
 
        if not has_games:
            continue
 
        sports_active.append(sport)
 
        if classified["live"]:
            any_live = True
            sports_live.append(sport)
            all_final = False
 
        if classified["scheduled"]:
            any_scheduled = True
            all_final = False
 
        if classified["final"] and not classified["live"] and not classified["scheduled"]:
            sports_final.append(sport)
 
    # If no games found at all, not final
    if not sports_active:
        all_final = False
 
    status = {
        "any_live": any_live,
        "all_final": all_final and bool(sports_active),
        "any_scheduled": any_scheduled,
        "sports_active": sports_active,
        "sports_live": sports_live,
        "sports_final": sports_final,
        "brand": brand,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
 
    logger.info(
        f"[GAME STATE] {brand} | live={any_live} | "
        f"final={status['all_final']} | active={sports_active}"
    )
    return status
 
 
def slate_live(brand: str = "EE") -> bool:
    """True if any games are currently live."""
    return get_slate_status(brand)["any_live"]
 
 
def slate_final(brand: str = "EE") -> bool:
    """True if all games in the slate are final."""
    return get_slate_status(brand)["all_final"]
 
 
def games_scheduled(brand: str = "EE") -> bool:
    """True if any games are scheduled (not yet started)."""
    return get_slate_status(brand)["any_scheduled"]
 
 
def get_active_sports(brand: str = "EE") -> list:
    """Return list of sports with games today."""
    return get_slate_status(brand)["sports_active"]
 
 
if __name__ == "__main__":
    print("EE slate status:")
    status = get_slate_status("EE")
    for k, v in status.items():
        print(f"  {k}: {v}")
 
    print("\nCBC slate status:")
    status = get_slate_status("CBC")
    for k, v in status.items():
        print(f"  {k}: {v}")
