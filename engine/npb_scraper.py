import requests
import logging
from datetime import datetime, timedelta, date
from bs4 import BeautifulSoup
 
logger = logging.getLogger(__name__)
 
LEAGUE_AVG_NPB_RUNS = 4.1
NPB_YAHOO_URL = "https://baseball.yahoo.co.jp/npb/schedule/"
 
NPB_TEAM_MAP = {
    "巨人": "Giants", "阪神": "Tigers", "広島": "Carp",
    "ヤクルト": "Swallows", "DeNA": "BayStars", "中日": "Dragons",
    "ソフトバンク": "Hawks", "オリックス": "Buffaloes", "ロッテ": "Marines",
    "西武": "Lions", "楽天": "Eagles", "日本ハム": "Fighters",
}
 
 
def get_npb_game_date():
    now = datetime.utcnow()
    jst = now + timedelta(hours=9)
    return jst.date()
 
 
def scrape_npb_schedule(game_date: date = None):
    if game_date is None:
        game_date = get_npb_game_date()
    date_str = game_date.strftime("%Y-%m-%d")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "ja,en-US;q=0.9",
            "Referer": "https://baseball.yahoo.co.jp/",
        }
        params = {"date": date_str}
        resp = requests.get(NPB_YAHOO_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        games = []
        game_boxes = (
            soup.find_all("div", {"class": "bb-gameCard"}) or
            soup.find_all("li", {"class": "bb-score__item"}) or
            soup.find_all("table", {"class": "bb-score"})
        )
        for box in game_boxes:
            teams = box.find_all("p", {"class": "bb-gameCard__team"})
            if len(teams) < 2:
                teams = box.find_all("span", {"class": "team"})
            if len(teams) < 2:
                continue
            away_raw = teams[0].get_text(strip=True)
            home_raw = teams[1].get_text(strip=True)
            away_name = NPB_TEAM_MAP.get(away_raw, away_raw)
            home_name = NPB_TEAM_MAP.get(home_raw, home_raw)
            if away_name and home_name:
                home_proj, away_proj = _project_npb_score(home_name, away_name)
                games.append({
                    "team_a": away_name, "team_b": home_name,
                    "a_score": away_proj, "b_score": home_proj,
                    "total": round(away_proj + home_proj, 1),
                    "game_date": game_date, "league": "NPB",
                })
        if not games:
            logger.warning("NPB Yahoo: no games parsed - trying fallback")
            return _get_npb_fallback(game_date)
        logger.info("NPB Yahoo: " + str(len(games)) + " games for " + date_str)
        return games
    except Exception as e:
        logger.error("NPB Yahoo scrape failed: " + str(e))
        return _get_npb_fallback(game_date)
 
 
def _get_npb_fallback(game_date: date):
    try:
        date_str = game_date.strftime("%Y%m%d")
        url = "https://site.api.espn.com/apis/site/v2/sports/baseball/npb/scoreboard"
        resp = requests.get(url, params={"dates": date_str}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        games = []
        for event in data.get("events", []):
            competitors = event.get("competitions", [{}])[0].get("competitors", [])
            home = next((c.get("team", {}).get("displayName", "") for c in competitors if c.get("homeAway") == "home"), "")
            away = next((c.get("team", {}).get("displayName", "") for c in competitors if c.get("homeAway") == "away"), "")
            if home and away:
                home_proj, away_proj = _project_npb_score(home, away)
                games.append({
                    "team_a": away, "team_b": home,
                    "a_score": away_proj, "b_score": home_proj,
                    "total": round(away_proj + home_proj, 1),
                    "game_date": game_date, "league": "NPB",
                })
        logger.info("NPB ESPN fallback: " + str(len(games)) + " games")
        return games
    except Exception as e:
        logger.error("NPB ESPN fallback failed: " + str(e))
        return []
 
 
def _project_npb_score(home_team, away_team):
    home = round(LEAGUE_AVG_NPB_RUNS * 1.02, 1)
    away = round(LEAGUE_AVG_NPB_RUNS * 0.98, 1)
    return home, away
 
 
def get_npb_projections(game_date: date = None):
    gd = game_date or get_npb_game_date()
    games = scrape_npb_schedule(gd)
    logger.info("NPB: " + str(len(games)) + " games found for " + str(gd))
    from engine.global_clv_helper import attach_clv_to_list
return attach_clv_to_list(games)

