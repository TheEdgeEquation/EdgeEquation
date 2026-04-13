import requests
import logging
import os
import json
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
CLV_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "clv_tracker.json")
 
 
def american_to_implied(odds):
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)
 
 
def fetch_closing_lines():
    if not ODDS_API_KEY:
        return {}
    try:
        url = ODDS_API_BASE + "/sports/baseball_mlb/odds"
        params = {"apiKey": ODDS_API_KEY, "regions": "us", "markets": "h2h,spreads,totals", "oddsFormat": "american"}
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            return {}
        games = resp.json()
        lines = {}
        for game in games:
            key = game.get("away_team", "") + "@" + game.get("home_team", "")
            for bm in game.get("bookmakers", [])[:1]:
                for mkt in bm.get("markets", []):
                    for outcome in mkt.get("outcomes", []):
                        lines[key + "_" + mkt.get("key", "") + "_" + outcome.get("name", "")] = outcome.get("price", -110)
        return lines
    except Exception as e:
        logger.error("Closing lines fetch failed: " + str(e))
        return {}
 
 
def calculate_clv(play, closing_lines):
    try:
        team = play.get("team", "")
        opp = play.get("opponent", "")
        game_key = opp + "@" + team
        opening_odds = play.get("over_odds", -115)
        opening_implied = american_to_implied(opening_odds)
        closing_key = game_key + "_pitcher_strikeouts_" + play.get("player", "")
        closing_odds = closing_lines.get(closing_key)
        if not closing_odds:
            return None
        closing_implied = american_to_implied(closing_odds)
        clv = round(closing_implied - opening_implied, 4)
        return clv
    except Exception as e:
        logger.error("CLV calc failed: " + str(e))
        return None
 
 
def track_clv_for_plays(plays):
    closing_lines = fetch_closing_lines()
    if not closing_lines:
        logger.info("No closing lines available for CLV tracking")
        return plays
    updated = []
    clv_plays = []
    for play in plays:
        clv = calculate_clv(play, closing_lines)
        updated_play = {**play, "closing_lines_checked": True}
        if clv is not None:
            updated_play["clv"] = clv
            if clv > 0.01:
                clv_plays.append(updated_play)
                logger.info("CLV: " + play.get("player", "") + " clv=" + str(clv))
        updated.append(updated_play)
    if clv_plays:
        _save_clv_alert(clv_plays)
    return updated
 
 
def _save_clv_alert(clv_plays):
    try:
        os.makedirs(os.path.dirname(CLV_FILE), exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")
        alerts = []
        if os.path.exists(CLV_FILE):
            with open(CLV_FILE, "r") as f:
                alerts = json.load(f)
        for play in clv_plays:
            alerts.append({
                "date": date_str,
                "player": play.get("player", ""),
                "clv": play.get("clv", 0),
                "opening_odds": play.get("over_odds", -115),
                "play_label": play.get("prop_label", ""),
                "line": play.get("line", 0),
            })
        with open(CLV_FILE, "w") as f:
            json.dump(alerts, f, indent=2)
        logger.info("CLV alert saved for " + str(len(clv_plays)) + " plays")
    except Exception as e:
        logger.error("CLV save failed: " + str(e))
 
 
def generate_clv_post(clv_plays):
    if not clv_plays:
        return ""
    lines = ["THE EDGE EQUATION — CLOSING LINE VALUE", datetime.now().strftime("%B %d"), ""]
    lines.append("The market moved in our direction after we posted:")
    lines.append("")
    for play in clv_plays[:3]:
        clv = play.get("clv", 0)
        player = play.get("player", "")
        line = play.get("line", 0)
        prop = play.get("prop_label", "")
        opening = play.get("over_odds", -115)
        lines.append(player + " " + str(line) + " " + prop)
        lines.append("Posted at " + str(opening) + " — line moved +" + str(round(clv*100, 1)) + "% implied")
        lines.append("")
    lines += ["The model found edge before the market did.", "That is closing line value.", "That is real edge.", "", "No feelings. Just facts.", "#EdgeEquation #CLV"]
    return "\n".join(lines)
 
 
def get_avg_clv():
    try:
        if not os.path.exists(CLV_FILE):
            return 0.0
        with open(CLV_FILE, "r") as f:
            alerts = json.load(f)
        if not alerts:
            return 0.0
        return round(sum(a.get("clv", 0) for a in alerts) / len(alerts) * 100, 1)
    except Exception:
        return 0.0
