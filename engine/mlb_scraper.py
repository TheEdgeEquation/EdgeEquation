import requests
import logging
from datetime import datetime, timedelta, date

logger = logging.getLogger(__name__)

LEAGUE_AVG_MLB_RUNS = 4.6

MLB_SCHEDULE_URL = (
    "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}"
)


def get_mlb_game_date():
    now = datetime.utcnow()
    est = now - timedelta(hours=5)
    return est.date()


# ─────────────────────────────────────────────
# MLB OFFICIAL SCRAPER
# ─────────────────────────────────────────────

def scrape_mlb_schedule(game_date: date = None):
    if game_date is None:
        game_date = get_mlb_game_date()

    date_str = game_date.strftime("%Y-%m-%d")

    try:
        url = MLB_SCHEDULE_URL.format(date=date_str)
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        games = []
        dates = data.get("dates", [])
        if not dates:
            logger.info("MLB: no games found on official API")
            return []

        for game in dates[0].get("games", []):
            try:
                away = game["teams"]["away"]["team"]["name"]
                home = game["teams"]["home"]["team"]["name"]
            except Exception:
                continue

            home_proj, away_proj = _project_mlb_score(home, away)

            games.append({
                "sport": "mlb",
                "league": "MLB",
                "team_a": away,
                "team_b": home,
                "a_score": away_proj,
                "b_score": home_proj,
                "total": round(away_proj + home_proj, 1),
                "game_date": game_date,
            })

        logger.info(f"MLB scraper: {len(games)} games")
        return games

    except Exception as e:
        logger.error("MLB official scrape failed: " + str(e))
        return _get_mlb_espn_fallback(game_date)


# ─────────────────────────────────────────────
# ESPN FALLBACK
# ─────────────────────────────────────────────

def _get_mlb_espn_fallback(game_date: date):
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
        resp = requests.get(url, params={"dates": game_date.strftime("%Y%m%d")}, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        games = []

        for event in data.get("events", []):
            competitors = event.get("competitions", [{}])[0].get("competitors", [])

            home = next(
                (c["team"]["displayName"] for c in competitors if c.get("homeAway") == "home"),
                ""
            )
            away = next(
                (c["team"]["displayName"] for c in competitors if c.get("homeAway") == "away"),
                ""
            )

            if home and away:
                home_proj, away_proj = _project_mlb_score(home, away)
                games.append({
                    "sport": "mlb",
                    "league": "MLB",
                    "team_a": away,
                    "team_b": home,
                    "a_score": away_proj,
                    "b_score": home_proj,
                    "total": round(away_proj + home_proj, 1),
                    "game_date": game_date,
                })

        logger.info(f"MLB ESPN fallback: {len(games)} games")
        return games

    except Exception as e:
        logger.error("MLB ESPN fallback failed: " + str(e))
        return []


# ─────────────────────────────────────────────
# PROJECTION MODEL
# ─────────────────────────────────────────────

def _project_mlb_score(home_team, away_team):
    home = round(LEAGUE_AVG_MLB_RUNS * 1.03, 1)
    away = round(LEAGUE_AVG_MLB_RUNS * 0.97, 1)
    return home, away


# ─────────────────────────────────────────────
# PUBLIC ENTRYPOINT (GLOBAL PIPELINE)
# ─────────────────────────────────────────────

def get_mlb_projections(game_date: date = None):
    """
    Public MLB entrypoint — official MLB API + ESPN fallback,
    then global CLV → validation → schema enforcement.
    """
    try:
        games = scrape_mlb_schedule(game_date)

        if not games:
            logger.info("MLB: no games found for projections")
            return []

        logger.info(f"MLB projections: {len(games)} games")

        # GLOBAL PIPELINE
        from engine.global_clv_helper import attach_clv_to_list
        from engine.global_validator import validate_global_list
        from engine.global_schema_enforcer import enforce_schema_list

        games = attach_clv_to_list(games)
        games = validate_global_list(games)
        games = enforce_schema_list(games)

        return games

    except Exception as e:
        logger.error("MLB projections failed: " + str(e))
        return []
