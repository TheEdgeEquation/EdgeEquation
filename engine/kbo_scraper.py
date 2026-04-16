import requests
import logging
from datetime import datetime, timedelta, date
from bs4 import BeautifulSoup
 
logger = logging.getLogger(__name__)
 
LEAGUE_AVG_KBO_RUNS = 5.2
KBO_SCHEDULE_URL = "https://www.koreabaseball.com/Schedule/Schedule.aspx"
 
 
def get_kbo_game_date():
    now = datetime.utcnow()
    kst = now + timedelta(hours=9)
    return kst.date()
 
 
def scrape_kbo_schedule(game_date: date = None):
    if game_date is None:
        game_date = get_kbo_game_date()
    date_str = game_date.strftime("%Y%m%d")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.koreabaseball.com/",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
        }
        params = {"seriesId": "0", "gameDate": date_str}
        resp = requests.get(KBO_SCHEDULE_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        games = []
        schedule_table = soup.find("table", {"class": "tbl"}) or soup.find("table")
        if not schedule_table:
            logger.warning("KBO: no schedule table found for " + date_str)
            return []
        rows = schedule_table.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue
            text = [c.get_text(strip=True) for c in cols]
            away_name = ""
            home_name = ""
            for i, t in enumerate(text):
                if "vs" in t.lower() or "@" in t:
                    parts = t.replace("vs", "@").split("@")
                    if len(parts) == 2:
                        away_name = parts[0].strip()
                        home_name = parts[1].strip()
                        break
                if i + 2 < len(text) and text[i + 1] in ("vs", "VS", "@"):
                    away_name = t.strip()
                    home_name = text[i + 2].strip()
                    break
            if not away_name or not home_name:
                team_cells = row.find_all("span", {"class": "team"})
                if len(team_cells) >= 2:
                    away_name = team_cells[0].get_text(strip=True)
                    home_name = team_cells[1].get_text(strip=True)
            if away_name and home_name:
                home_proj, away_proj = _project_kbo_score(home_name, away_name)
                games.append({
                    "team_a": away_name,
                    "team_b": home_name,
                    "a_score": away_proj,
                    "b_score": home_proj,
                    "total": round(away_proj + home_proj, 1),
                    "game_date": game_date,
                    "league": "KBO",
                })
        logger.info("KBO scraper: " + str(len(games)) + " games for " + date_str)
        return games
    except Exception as e:
        logger.error("KBO scrape failed: " + str(e))
        return _get_kbo_espn_fallback(game_date)
 
 
def _get_kbo_espn_fallback(game_date: date):
    try:
        date_str = game_date.strftime("%Y%m%d")
        url = "https://site.api.espn.com/apis/site/v2/sports/baseball/kbo/scoreboard"
        resp = requests.get(url, params={"dates": date_str}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        games = []
        for event in data.get("events", []):
            competitors = event.get("competitions", [{}])[0].get("competitors", [])
            home = next((c.get("team", {}).get("displayName", "") for c in competitors if c.get("homeAway") == "home"), "")
            away = next((c.get("team", {}).get("displayName", "") for c in competitors if c.get("homeAway") == "away"), "")
            if home and away:
                home_proj, away_proj = _project_kbo_score(home, away)
                games.append({
                    "team_a": away, "team_b": home,
                    "a_score": away_proj, "b_score": home_proj,
                    "total": round(away_proj + home_proj, 1),
                    "game_date": game_date, "league": "KBO",
                })
        logger.info("KBO ESPN fallback: " + str(len(games)) + " games")
        return games
    except Exception as e:
        logger.error("KBO ESPN fallback failed: " + str(e))
        return []
 
 
def _project_kbo_score(home_team, away_team):
    home = round(LEAGUE_AVG_KBO_RUNS * 1.03, 1)
    away = round(LEAGUE_AVG_KBO_RUNS * 0.97, 1)
    return home, away
 
  def get_kbo_projections(game_date: date = None):
    """
    Public KBO entrypoint — uses official schedule + ESPN fallback,
    then runs through the global pipeline.
    """
    try:
        games = scrape_kbo_schedule(game_date)

        if not games:
            logger.info("KBO: no games found for projections")
            return []

        logger.info("KBO projections: " + str(len(games)) + " games")

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
        logger.error("KBO projections failed: " + str(e))
        return []


