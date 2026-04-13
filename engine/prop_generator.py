import requests
import logging
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
MLB_API = "https://statsapi.mlb.com/api/v1"
CURRENT_YEAR = datetime.now().year
 
TYPICAL_K_LINES = {
    (0, 4.0):  {"line": 3.5, "over_odds": -115, "under_odds": -105},
    (4.0, 5.0): {"line": 4.5, "over_odds": -115, "under_odds": -105},
    (5.0, 6.0): {"line": 5.5, "over_odds": -115, "under_odds": -105},
    (6.0, 7.0): {"line": 6.5, "over_odds": -115, "under_odds": -105},
    (7.0, 8.0): {"line": 7.5, "over_odds": -115, "under_odds": -105},
    (8.0, 9.0): {"line": 8.5, "over_odds": -115, "under_odds": -105},
    (9.0, 99.0): {"line": 9.5, "over_odds": -115, "under_odds": -105},
}
 
 
def american_to_implied(odds):
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)
 
 
def get_line_for_lambda(true_lambda):
    for (low, high), data in TYPICAL_K_LINES.items():
        if low <= true_lambda < high:
            return data
    return {"line": round(true_lambda - 0.5, 1), "over_odds": -115, "under_odds": -105}
 
 
def get_todays_starters():
    try:
        url = MLB_API + "/schedule"
        params = {
            "sportId": 1,
            "hydrate": "probablePitcher,team",
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        starters = []
        for date in data.get("dates", []):
            for game in date.get("games", []):
                home = game.get("teams", {}).get("home", {})
                away = game.get("teams", {}).get("away", {})
                home_team = home.get("team", {}).get("name", "")
                away_team = away.get("team", {}).get("name", "")
                home_pitcher = home.get("probablePitcher", {}).get("fullName", "")
                away_pitcher = away.get("probablePitcher", {}).get("fullName", "")
                commence = game.get("gameDate", "")
                if home_pitcher:
                    starters.append({
                        "player": home_pitcher,
                        "team": home_team,
                        "opponent": away_team,
                        "home": True,
                        "commence_time": commence,
                        "sport": "baseball_mlb",
                        "sport_label": "MLB",
                        "prop_label": "K",
                        "icon": "⚾",
                    })
                if away_pitcher:
                    starters.append({
                        "player": away_pitcher,
                        "team": away_team,
                        "opponent": home_team,
                        "home": False,
                        "commence_time": commence,
                        "sport": "baseball_mlb",
                        "sport_label": "MLB",
                        "prop_label": "K",
                        "icon": "⚾",
                    })
        logger.info("Found " + str(len(starters)) + " starters today")
        return starters
    except Exception as e:
        logger.error("Failed to fetch starters: " + str(e))
        return []
 
 
def generate_k_props():
    from engine.stats.mlb_stats import get_full_pitcher_profile
    from engine.stats.weather import get_weather
    from engine.stats.umpire import get_umpire_for_game
    from engine.stats.park_factors import get_k_factor, get_altitude_adjustment
    from engine.stats.savant import get_blended_savant_stats, get_swstr_k_adjustment, get_pitch_mix_adjustment
 
    starters = get_todays_starters()
    if not starters:
        logger.warning("No starters found today")
        return []
 
    props = []
    for starter in starters:
        try:
            player = starter["player"]
            home_team = starter["team"] if starter["home"] else starter["opponent"]
            away_team = starter["opponent"] if starter["home"] else starter["team"]
 
            logger.info("Generating K prop for " + player)
 
            profile = get_full_pitcher_profile(player, starter["opponent"], home_team)
            k9_season = profile.get("k9_season", 8.0)
            k9_recent = profile.get("k9_recent", k9_season)
            avg_ip = profile.get("avg_ip_recent", 5.5)
            k9_blended = (k9_recent * 0.60) + (k9_season * 0.40)
            base_lambda = (k9_blended / 9.0) * avg_ip
 
            opp_adj = profile.get("opp_k_adjustment", 1.0)
            platoon_adj = profile.get("platoon_adjustment", 1.0)
            weather = get_weather(home_team)
            weather_adj = weather.get("k_adjustment", 1.0)
            umpire_name, umpire_adj = get_umpire_for_game(home_team, away_team)
            park_adj = get_k_factor(home_team)
            alt_adj = get_altitude_adjustment(home_team)
 
            player_id = profile.get("player_id")
            swstr_adj = 1.0
            pitch_mix_adj = 1.0
            if player_id:
                savant = get_blended_savant_stats(player_id)
                swstr_adj = get_swstr_k_adjustment(savant.get("swstr_pct", 0.107))
                pitch_mix_adj = get_pitch_mix_adjustment(savant.get("breaking_ball_pct", 0.28))
 
            true_lambda = round(
                base_lambda * opp_adj * platoon_adj * weather_adj
                * umpire_adj * park_adj * alt_adj * swstr_adj * pitch_mix_adj, 3
            )
 
            line_data = get_line_for_lambda(true_lambda)
            line = line_data["line"]
            over_odds = line_data["over_odds"]
            under_odds = line_data["under_odds"]
            implied = american_to_implied(over_odds)
 
            logger.info(player + ": true_lambda=" + str(true_lambda) + " line=" + str(line) + " odds=" + str(over_odds))
 
            props.append({
                **starter,
                "line": line,
                "over_odds": over_odds,
                "under_odds": under_odds,
                "implied_prob": round(implied, 4),
                "true_lambda": true_lambda,
                "source": "model_generated",
            })
 
        except Exception as e:
            logger.error("K prop generation failed for " + starter.get("player", "") + ": " + str(e))
            continue
 
    logger.info("Generated " + str(len(props)) + " K props from model")
    return props
