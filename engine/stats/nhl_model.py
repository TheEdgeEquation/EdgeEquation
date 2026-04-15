import logging
import math
 
logger = logging.getLogger(__name__)
 
LEAGUE_AVG_SOG = 3.2
LEAGUE_AVG_SOG_ALLOWED = 30.5
 
NHL_SOG_LINE_TABLE = {
    (0, 2.0): {"line": 1.5, "over_odds": -115, "under_odds": -105},
    (2.0, 3.0): {"line": 2.5, "over_odds": -115, "under_odds": -105},
    (3.0, 4.0): {"line": 3.5, "over_odds": -115, "under_odds": -105},
    (4.0, 5.0): {"line": 4.5, "over_odds": -115, "under_odds": -105},
    (5.0, 6.0): {"line": 5.5, "over_odds": -115, "under_odds": -105},
    (6.0, 99.0): {"line": 6.5, "over_odds": -115, "under_odds": -105},
}
 
 
def get_line_for_lambda(true_lambda, table):
    for (low, high), data in table.items():
        if low <= true_lambda < high:
            return data
    return {"line": round(true_lambda - 0.5, 1), "over_odds": -115, "under_odds": -105}
 
 
def calculate_sog_lambda(profile, home=False):
    try:
        sog_per_game = profile.get("sog_per_game", LEAGUE_AVG_SOG)
        opp_adj = profile.get("opp_sog_adj", 1.0)
        home_adj = 1.03 if home else 0.98
        true_lambda = sog_per_game * opp_adj * home_adj
        logger.info("SOG lambda: sog=" + str(sog_per_game) + " opp=" + str(opp_adj) + " home=" + str(home_adj) + " = " + str(round(true_lambda, 3)))
        return round(true_lambda, 3)
    except Exception as e:
        logger.error("SOG lambda failed: " + str(e))
        return LEAGUE_AVG_SOG
 
 
def generate_nhl_props(players_with_profiles):
    props = []
    for item in players_with_profiles:
        player = item.get("player_name", "")
        profile = item.get("profile", {})
        team = item.get("team", "")
        opponent = item.get("opponent", "")
        home = item.get("home", False)
        commence = item.get("commence_time", "")
        lam_sog = calculate_sog_lambda(profile, home)
        if lam_sog > 1.5:
            line_data = get_line_for_lambda(lam_sog, NHL_SOG_LINE_TABLE)
            props.append({
                "player": player, "team": team, "opponent": opponent,
                "sport": "icehockey_nhl", "sport_label": "NHL", "prop_label": "SOG", "icon": "🏒",
                "line": line_data["line"], "over_odds": line_data["over_odds"], "under_odds": line_data["under_odds"],
                "implied_prob": round(abs(line_data["over_odds"]) / (abs(line_data["over_odds"]) + 100), 4),
                "true_lambda": lam_sog, "source": "model_generated", "commence_time": commence,
                "sog_per_60": profile.get("sog_per_60", 4.8),
                "avg_toi": profile.get("avg_toi", 18.0),
                "opp_sog_allowed": profile.get("opp_sog_allowed", LEAGUE_AVG_SOG_ALLOWED),
            })
    logger.info("Generated " + str(len(props)) + " NHL props")
    return props
