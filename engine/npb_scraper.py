import requests
import logging
from datetime import datetime, timedelta, date
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

LEAGUE_AVG_NPB_RUNS = 4.1
NPB_SCHEDULE_URL = "https://npb.jp/bis/eng/2026/games/"


def get_npb_game_date():
    now = datetime.utcnow()
    jst = now + timedelta(hours=9)
    return jst.date()


def scrape_npb_schedule(game_date: date = None):
    if game_date is None:
        game_date = get_npb_game_date()

    try:
        resp = requests.get(NPB_SCHEDULE_URL, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        games = []
        rows = soup.select("table tr")

        for row in rows:
            cells = row.select("td")
            if len(cells) < 3:
                continue

            away = cells[0].get_text(strip=True)
            home = cells[-1].get_text(strip=True)

            # Filter out headers / invalid rows
            if (
                not away or not home or
                len(away) < 2 or len(home) < 2 or
                away.lower() in ("away", "visitor", "team") or
                home.lower() in ("home", "team")
            ):
                continue

            home_proj, away_proj = _project_npb_score(home, away)

            games.append({
                "sport": "npb",
                "league": "NPB",
                "team_a": away,
                "team_b": home,
                "a_score": away_proj,
                "b_score": home_proj,
                "total": round(away_proj + home_proj, 1),
                "game_date": game_date,
            })

        logger.info(f"NPB scraper: {len(games)} games")
        return games

    except Exception as e:
        logger.error("NPB scrape failed: " + str(e))
        return _get_npb_espn_fallback(game_date)


def _get_npb_espn_fallback(game_date: date):
    """
    ESPN fallback — NPB is under 'baseball/npb'
    """
    try:
        date_str = game_date.strftime("%Y%m%d")
        url = "https://site.api.espn.com/apis/site/v2/sports/baseball/npb/scoreboard"

        resp = requests.get(url, params={"dates": date_str}, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        games = []
        for event in data.get("events", []):
            competitors = event.get("competitions", [{}])[0].get("competitors", [])

            home = next(
                (c.get("team", {}).get("displayName", "") for c in competitors if c.get("homeAway") == "home"),
                ""
            )
            away = next(
                (c.get("team", {}).get("displayName", "") for c in competitors if c.get("homeAway") == "away"),
                ""
            )

            if home and away:
                home_proj, away_proj = _project_npb_score(home, away)
                games.append({
                    "sport": "npb",
                    "league": "NPB",
                    "team_a": away,
                    "team_b": home,
                    "a_score": away_proj,
                    "b_score": home_proj,
                    "total": round(away_proj + home_proj, 1),
                    "game_date": game_date,
                })

        logger.info(f"NPB ESPN fallback: {len(games)} games")
        return games

    except Exception as e:
        logger.error("NPB ESPN fallback failed: " + str(e))
        return []


def _project_npb_score(home_team, away_team):
    home = round(LEAGUE_AVG_NPB_RUNS * 1.02, 1)
    away = round(LEAGUE_AVG_NPB_RUNS * 0.98, 1)
    return home, away


def get_npb_projections(game_date: date = None):
    """
    Public NPB entrypoint — official site + ESPN fallback,
    then global CLV → validation → schema enforcement.
    """
    try:
        games = scrape_npb_schedule(game_date)

        if not games:
            logger.info("NPB: no games found for projections")
            return []

        logger.info("NPB projections: " + str(len(games)) + " games")

        # --- GLOBAL CLV ---
        from engine.global_clv_helper import attach_clv_to_list
        games = attach_clv_to_list(games)

        # --- GLOBAL VALIDATION ---
        from engine.global_validator import validate_global_list
        games = validate_global_list(games)

        # --- GLOBAL SCHEMA ENFORCER ---
        from engine.global_schema_enforcer import enforce_schema_list
        games = enforce_schema_list(games)

        return games

    except Exception as e:
        logger.error("NPB projections failed: " + str(e))
        return []
