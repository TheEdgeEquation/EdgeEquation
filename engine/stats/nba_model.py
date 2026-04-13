import logging
import math
 
logger = logging.getLogger(__name__)
 
LEAGUE_AVG_PACE = 99.0
LEAGUE_AVG_3PA = 12.0
 
NBA_LINE_TABLE = {
    (0, 1.5): {"line": 1.5, "over_odds": -115, "under_odds": -105},
    (1.5, 2.5): {"line": 2.5, "over_odds": -115, "under_odds": -105},
    (2.5, 3.5): {"line": 3.5, "over_odds": -115, "under_odds": -105},
    (3.5, 4.5): {"line": 4.5, "over_odds": -115, "under_odds": -105},
    (4.5, 5.5): {"line": 5.5, "over_odds": -115, "under_odds": -105},
    (5.5, 6.5): {"line": 6.5, "over_odds": -115, "under_odds": -105},
    (6.5, 99.0): {"line": 7.5, "over_odds": -115, "under_odds": -105},
}
 
PTS_LINE_TABLE = {
    (0, 10): {"line": 9.5, "over_odds": -115, "under_odds": -105},
    (10, 15): {"line": 14.5, "over_odds": -115, "under_odds": -105},
    (15, 20): {"line": 19.5, "over_odds": -115, "under_odds": -105},
    (20, 25): {"line": 24.5, "over_odds": -115, "under_odds": -105},
    (25, 30): {"line": 29.5, "over_odds": -115, "under_odds": -105},
    (30, 35): {"line": 34.5, "over_odds": -115, "under_odds": -105},
    (35, 99): {"line": 39.5, "over_odds": -115, "under_odds": -105},
}
 
 
def get_line_for_lambda(true_lambda, table):
    for (low, high), data in table.items():
        if low <= true_lambda < high:
            return data
    return {"line": round(true_lambda - 0.5, 1), "over_odds": -115, "under_odds": -105}
 
 
def calculate_3pm_lambda(profile, home=False):
    try:
        fg3a = profile.get("fg3a_blended", 8.0)
        fg3_pct = profile.get("fg3_pct", 0.36)
        opp_adj = profile.get("opp_3p_adj", 1.0)
        rest_adj = profile.get("rest_adj", 1.0)
        home_adj = 1.02 if home else 0.99
        true_lambda = fg3a * fg3_pct * opp_adj * rest_adj * home_adj
        logger.info("3PM lambda: fg3a=" + str(fg3a) + " pct=" + str(fg3_pct) + " opp=" + str(opp_adj) + " rest=" + str(rest_adj) + " = " + str(round(true_lambda, 3)))
        return round(true_lambda, 3)
    except Exception as e:
        logger.error("3PM lambda failed: " + str(e))
        return 2.5
 
 
def calculate_pts_lambda(profile, home=False):
    try:
        pts = profile.get("pts_blended", 18.0)
        rest_adj = profile.get("rest_adj", 1.0)
        home_adj = 1.02 if home else 0.99
        true_lambda = pts * rest_adj * home_adj
        return round(true_lambda, 2)
    except Exception as e:
        return 18.0
 
 
def calculate_ast_lambda(profile, home=False):
    try:
        ast = profile.get("ast_blended", 4.0)
        rest_adj = profile.get("rest_adj", 1.0)
        return round(ast * rest_adj, 2)
    except Exception:
        return 4.0
 
 
def calculate_reb_lambda(profile, home=False):
    try:
        reb = profile.get("reb_blended", 4.0)
        rest_adj = profile.get("rest_adj", 1.0)
        return round(reb * rest_adj, 2)
    except Exception:
        return 4.0
 
 
def generate_nba_props(players_with_profiles):
    props = []
    for item in players_with_profiles:
        player = item.get("player_name", "")
        profile = item.get("profile", {})
        team = item.get("team", "")
        opponent = item.get("opponent", "")
        home = item.get("home", False)
        sport = "basketball_nba"
        sport_label = "NBA"
        commence = item.get("commence_time", "")
        lam_3pm = calculate_3pm_lambda(profile, home)
        if lam_3pm > 1.5:
            line_data = get_line_for_lambda(lam_3pm, NBA_LINE_TABLE)
            props.append({
                "player": player, "team": team, "opponent": opponent,
                "sport": sport, "sport_label": sport_label, "prop_label": "3PM", "icon": "🏀",
                "line": line_data["line"], "over_odds": line_data["over_odds"], "under_odds": line_data["under_odds"],
                "implied_prob": round(abs(line_data["over_odds"]) / (abs(line_data["over_odds"]) + 100), 4),
                "true_lambda": lam_3pm, "source": "model_generated", "commence_time": commence,
                "attempts_per_game": profile.get("fg3a_blended", 8.0),
                "opp_defense_rate": profile.get("opp_3pa_allowed", LEAGUE_AVG_3PA),
                "pace_label": "average",
            })
        lam_pts = calculate_pts_lambda(profile, home)
        if lam_pts > 10:
            line_data = get_line_for_lambda(lam_pts, PTS_LINE_TABLE)
            props.append({
                "player": player, "team": team, "opponent": opponent,
                "sport": sport, "sport_label": sport_label, "prop_label": "PTS", "icon": "🏀",
                "line": line_data["line"], "over_odds": line_data["over_odds"], "under_odds": line_data["under_odds"],
                "implied_prob": round(abs(line_data["over_odds"]) / (abs(line_data["over_odds"]) + 100), 4),
                "true_lambda": lam_pts, "source": "model_generated", "commence_time": commence,
            })
    logger.info("Generated " + str(len(props)) + " NBA props")
    return props
