import requests
import logging
from datetime import datetime, timedelta, date
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

LEAGUE_AVG_KBO_RUNS = 5.2
LEAGUE_AVG_NPB_RUNS = 4.1

KBO_SCHEDULE_URL = "https://www.koreabaseball.com/Schedule/Schedule.aspx"
NPB_SCHEDULE_URL = "https://npb.jp/bis/eng/2026/games/"


# ─────────────────────────────────────────────
# TIME HELPERS
# ─────────────────────────────────────────────

def get_kbo_game_date():
    now = datetime.utcnow()
    return (now + timedelta(hours=9)).date()  # KST


def get_npb_game_date():
    now = datetime.utcnow()
    return (now + timedelta(hours=9)).date()  # JST


# ─────────────────────────────────────────────
# KBO SCRAPER
# ─────────────────────────────────────────────

def scrape_kbo_schedule(game_date: date = None):
    if game_date is None:
        game_date = get_kbo_game_date()
    date_str = game_date.strftime("%Y%m%d")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.koreabaseball.com/",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
        }
        params = {"seriesId": "0", "gameDate": date_str}

        resp = requests.get(KBO_SCHEDULE_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        games = []
        table = soup.find("table", {"class": "tbl"}) or soup.find("table")
        if not table:
            logger.warning("KBO: no schedule table found for " + date_str)
            return []

        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            text = [c.get_text(strip=True) for c in cols]
            away, home = "", ""

            # Parse "Away vs Home" or "Away @ Home"
            for i, t in enumerate(text):
                if "vs" in t.lower() or "@" in t:
                    parts = t.replace("vs", "@").split("@")
                    if len(parts) == 2:
                        away, home = parts[0].strip(), parts[1].strip()
                        break
                if i + 2 < len(text) and text[i + 1] in ("vs", "VS", "@"):
                    away, home = t.strip(), text[i + 2].strip()
                    break

            # Fallback: span.team
            if not away or not home:
                teams = row.find_all("span", {"class": "team"})
                if len(teams) >= 2:
                    away = teams[0].get_text(strip=True)
                    home = teams[1].get_text(strip=True)

            if away and home:
                home_proj, away_proj = _project_kbo_score(home, away)
                games.append({
                    "sport": "kbo",
                    "league": "KBO",
                    "team_a": away,
                    "team_b": home,
                    "a_score": away_proj,
                    "b_score": home_proj,
                    "total": round(away_proj + home_proj, 1),
                    "game_date": game_date,
                })

        logger.info(f"KBO scraper: {len(games)} games")
        return games

    except Exception as e:
        logger.error("KBO scrape failed: " + str(e))
        return _get_kbo_espn_fallback(game_date)


def _get_kbo_espn_fallback(game_date: date):
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/baseball/kbo/scoreboard"
        resp = requests.get(url, params={"dates": game_date.strftime("%Y%m%d")}, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        games = []
        for event in data.get("events", []):
            competitors = event.get("competitions", [{}])[0].get("competitors", [])

            home = next((c["team"]["displayName"] for c in competitors if c.get("homeAway") == "home"), "")
            away = next((c["team"]["displayName"] for c in competitors if c.get("homeAway") == "away"), "")

            if home and away:
                home_proj, away_proj = _project_kbo_score(home, away)
                games.append({
                    "sport": "kbo",
                    "league": "KBO",
                    "team_a": away,
                    "team_b": home,
                    "a_score": away_proj,
                    "b_score": home_proj,
                    "total": round(away_proj + home_proj, 1),
                    "game_date": game_date,
                })

        logger.info(f"KBO ESPN fallback: {len(games)} games")
        return games

    except Exception as e:
        logger.error("KBO ESPN fallback failed: " + str(e))
        return []


def _project_kbo_score(home_team, away_team):
    home = round(LEAGUE_AVG_KBO_RUNS * 1.03, 1)
    away = round(LEAGUE_AVG_KBO_RUNS * 0.97, 1)
    return home, away


def get_kbo_projections(game_date: date = None):
    try:
        games = scrape_kbo_schedule(game_date)
        if not games:
            return []

        # GLOBAL PIPELINE
        from engine.global_clv_helper import attach_clv_to_list
        from engine.global_validator import validate_global_list
        from engine.global_schema_enforcer import enforce_schema_list

        games = attach_clv_to_list(games)
        games = validate_global_list(games)
        games = enforce_schema_list(games)

        return games

    except Exception as e:
        logger.error("KBO projections failed: " + str(e))
        return []


# ─────────────────────────────────────────────
# NPB SCRAPER
# ─────────────────────────────────────────────

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

            if (
                not away or not home or
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
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/baseball/npb/scoreboard"
        resp = requests.get(url, params={"dates": game_date.strftime("%Y%m%d")}, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        games = []
        for event in data.get("events", []):
            competitors = event.get("competitions", [{}])[0].get("competitors", [])

            home = next((c["team"]["displayName"] for c in competitors if c.get("homeAway") == "home"), "")
            away = next((c["team"]["displayName"] for c in competitors if c.get("homeAway") == "away"), "")

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
    try:
        games = scrape_npb_schedule(game_date)
        if not games:
            return []

        # GLOBAL PIPELINE
        from engine.global_clv_helper import attach_clv_to_list
        from engine.global_validator import validate_global_list
        from engine.global_schema_enforcer import enforce_schema_list

        games = attach_clv_to_list(games)
        games = validate_global_list(games)
        games = enforce_schema_list(games)

        return games

    except Exception as e:
        logger.error("NPB projections failed: " + str(e))
        return []
