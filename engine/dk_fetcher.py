import requests
import logging
import json
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
DK_BASE = "https://sportsbook.draftkings.com/api/odds/v1"
 
DK_MLB_CATEGORIES = {
    "pitcher_strikeouts": {"category": 1000, "subcategory": 6998},
    "pitcher_strikeouts_alt": {"category": 1000, "subcategory": 7003},
    "batter_hits": {"category": 1000, "subcategory": 7001},
    "batter_total_bases": {"category": 1000, "subcategory": 7002},
}
 
DK_NBA_CATEGORIES = {
    "player_threes": {"category": 583, "subcategory": 10589},
    "player_points": {"category": 583, "subcategory": 10588},
    "player_assists": {"category": 583, "subcategory": 10590},
    "player_rebounds": {"category": 583, "subcategory": 10591},
}
 
DK_NHL_CATEGORIES = {
    "player_shots": {"category": 1064, "subcategory": 10574},
    "player_goals": {"category": 1064, "subcategory": 10573},
}
 
DK_LEAGUE_IDS = {
    "baseball_mlb": 84240,
    "basketball_nba": 42648,
    "icehockey_nhl": 42133,
}
 
 
def american_to_implied(odds):
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)
 
 
def fetch_dk_props(league, category_id, subcategory_id):
    try:
        league_id = DK_LEAGUE_IDS.get(league)
        if not league_id:
            return []
        url = DK_BASE + "/leagues/" + str(league_id) + "/categories/" + str(category_id) + "/subcategories/" + str(subcategory_id)
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
            "Accept": "application/json",
            "Referer": "https://sportsbook.draftkings.com/",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 404:
            logger.warning("DK market not available: " + league + " cat=" + str(category_id) + " sub=" + str(subcategory_id))
            return []
        resp.raise_for_status()
        return resp.json().get("eventGroup", {}).get("offerCategories", [])
    except Exception as e:
        logger.error("DK fetch failed: " + str(e))
        return []
 
 
def parse_dk_pitcher_strikeouts(data, sport_label="MLB"):
    props = []
    try:
        for cat in data:
            for subcat in cat.get("offerSubcategoryDescriptors", []):
                for offer_cat in subcat.get("offerSubcategory", {}).get("offers", []):
                    for offer in offer_cat:
                        event_name = offer.get("label", "")
                        participants = offer.get("outcomes", [])
                        player_name = ""
                        over_odds = None
                        under_odds = None
                        line = None
                        for outcome in participants:
                            label = outcome.get("label", "").lower()
                            odds = outcome.get("oddsAmerican", "")
                            line_val = outcome.get("line", None)
                            try:
                                odds_int = int(odds)
                            except Exception:
                                continue
                            if line_val is not None:
                                try:
                                    line = float(line_val)
                                except Exception:
                                    pass
                            participant = outcome.get("participant", "")
                            if participant:
                                player_name = participant
                            if "over" in label:
                                over_odds = odds_int
                            elif "under" in label:
                                under_odds = odds_int
                        if player_name and line is not None and over_odds is not None:
                            implied = american_to_implied(over_odds)
                            parts = event_name.split(" @ ") if " @ " in event_name else event_name.split(" vs ")
                            away = parts[0].strip() if len(parts) > 1 else ""
                            home = parts[1].strip() if len(parts) > 1 else ""
                            props.append({
                                "player": player_name,
                                "team": home,
                                "opponent": away,
                                "sport": "baseball_mlb",
                                "sport_label": sport_label,
                                "prop_label": "K",
                                "icon": "⚾",
                                "line": line,
                                "over_odds": over_odds,
                                "under_odds": under_odds or -110,
                                "implied_prob": round(implied, 4),
                                "source": "draftkings",
                            })
        logger.info("Parsed " + str(len(props)) + " pitcher K props from DK")
    except Exception as e:
        logger.error("DK parse failed: " + str(e))
    return props
 
 
def parse_dk_player_props(data, sport, prop_label, icon):
    props = []
    try:
        for cat in data:
            for subcat in cat.get("offerSubcategoryDescriptors", []):
                for offer_cat in subcat.get("offerSubcategory", {}).get("offers", []):
                    for offer in offer_cat:
                        event_name = offer.get("label", "")
                        player_name = ""
                        over_odds = None
                        under_odds = None
                        line = None
                        for outcome in offer.get("outcomes", []):
                            label = outcome.get("label", "").lower()
                            odds = outcome.get("oddsAmerican", "")
                            line_val = outcome.get("line", None)
                            try:
                                odds_int = int(odds)
                            except Exception:
                                continue
                            if line_val is not None:
                                try:
                                    line = float(line_val)
                                except Exception:
                                    pass
                            participant = outcome.get("participant", "")
                            if participant:
                                player_name = participant
                            if "over" in label:
                                over_odds = odds_int
                            elif "under" in label:
                                under_odds = odds_int
                        if player_name and line is not None and over_odds is not None:
                            implied = american_to_implied(over_odds)
                            parts = event_name.split(" @ ") if " @ " in event_name else event_name.split(" vs ")
                            away = parts[0].strip() if len(parts) > 1 else ""
                            home = parts[1].strip() if len(parts) > 1 else ""
                            props.append({
                                "player": player_name,
                                "team": home,
                                "opponent": away,
                                "sport": sport,
                                "sport_label": sport.split("_")[1].upper() if "_" in sport else sport.upper(),
                                "prop_label": prop_label,
                                "icon": icon,
                                "line": line,
                                "over_odds": over_odds,
                                "under_odds": under_odds or -110,
                                "implied_prob": round(implied, 4),
                                "source": "draftkings",
                            })
    except Exception as e:
        logger.error("DK props parse failed: " + str(e))
    return props
 
 
def fetch_all_dk_props():
    all_props = []
 
    logger.info("Fetching MLB pitcher strikeouts from DraftKings...")
    for key, ids in DK_MLB_CATEGORIES.items():
        if "strikeout" in key:
            data = fetch_dk_props("baseball_mlb", ids["category"], ids["subcategory"])
            if data:
                props = parse_dk_pitcher_strikeouts(data, "MLB")
                if props:
                    all_props.extend(props)
                    logger.info("DK MLB " + key + ": " + str(len(props)) + " props")
                    break
 
    logger.info("Fetching NBA player threes from DraftKings...")
    for key, ids in DK_NBA_CATEGORIES.items():
        if "three" in key:
            data = fetch_dk_props("basketball_nba", ids["category"], ids["subcategory"])
            if data:
                props = parse_dk_player_props(data, "basketball_nba", "3PM", "🏀")
                if props:
                    all_props.extend(props)
                    logger.info("DK NBA " + key + ": " + str(len(props)) + " props")
                    break
 
    logger.info("Fetching NHL shots on goal from DraftKings...")
    for key, ids in DK_NHL_CATEGORIES.items():
        if "shot" in key:
            data = fetch_dk_props("icehockey_nhl", ids["category"], ids["subcategory"])
            if data:
                props = parse_dk_player_props(data, "icehockey_nhl", "SOG", "🏒")
                if props:
                    all_props.extend(props)
                    logger.info("DK NHL " + key + ": " + str(len(props)) + " props")
                    break
 
    logger.info("DraftKings total props fetched: " + str(len(all_props)))
    return all_props
