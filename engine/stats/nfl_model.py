import logging
 
logger = logging.getLogger(__name__)
 
LEAGUE_AVG_PASS_YDS = 245.0
LEAGUE_AVG_REC_YDS = 65.0
LEAGUE_AVG_RUSH_YDS = 55.0
 
NFL_PASS_LINE_TABLE = {
    (0, 175): {"line": 174.5, "over_odds": -115, "under_odds": -105},
    (175, 200): {"line": 199.5, "over_odds": -115, "under_odds": -105},
    (200, 225): {"line": 224.5, "over_odds": -115, "under_odds": -105},
    (225, 250): {"line": 249.5, "over_odds": -115, "under_odds": -105},
    (250, 275): {"line": 274.5, "over_odds": -115, "under_odds": -105},
    (275, 300): {"line": 299.5, "over_odds": -115, "under_odds": -105},
    (300, 999): {"line": 324.5, "over_odds": -115, "under_odds": -105},
}
 
NFL_REC_LINE_TABLE = {
    (0, 35): {"line": 34.5, "over_odds": -115, "under_odds": -105},
    (35, 50): {"line": 49.5, "over_odds": -115, "under_odds": -105},
    (50, 65): {"line": 64.5, "over_odds": -115, "under_odds": -105},
    (65, 80): {"line": 79.5, "over_odds": -115, "under_odds": -105},
    (80, 100): {"line": 99.5, "over_odds": -115, "under_odds": -105},
    (100, 999): {"line": 124.5, "over_odds": -115, "under_odds": -105},
}
 
NFL_RUSH_LINE_TABLE = {
    (0, 40): {"line": 39.5, "over_odds": -115, "under_odds": -105},
    (40, 55): {"line": 54.5, "over_odds": -115, "under_odds": -105},
    (55, 70): {"line": 69.5, "over_odds": -115, "under_odds": -105},
    (70, 85): {"line": 84.5, "over_odds": -115, "under_odds": -105},
    (85, 999): {"line": 99.5, "over_odds": -115, "under_odds": -105},
}
 
 
def get_line_for_lambda(true_lambda, table):
    for (low, high), data in table.items():
        if low <= true_lambda < high:
            return data
    return {"line": round(true_lambda - 0.5, 1), "over_odds": -115, "under_odds": -105}
 
 
def generate_nfl_props(players_with_profiles):
    props = []
    for item in players_with_profiles:
        player = item.get("player_name", "")
        profile = item.get("profile", {})
        team = item.get("team", "")
        opponent = item.get("opponent", "")
        position = item.get("position", "WR")
        commence = item.get("commence_time", "")
        lam = profile.get("true_lambda", 0)
        prop_label = profile.get("prop_label", "RecYds")
        if prop_label == "PassYds":
            table = NFL_PASS_LINE_TABLE
            icon = "🏈"
        elif prop_label == "RecYds":
            table = NFL_REC_LINE_TABLE
            icon = "🏈"
        else:
            table = NFL_RUSH_LINE_TABLE
            icon = "🏈"
        if lam > 20:
            line_data = get_line_for_lambda(lam, table)
            props.append({
                "player": player, "team": team, "opponent": opponent,
                "sport": "americanfootball_nfl", "sport_label": "NFL", "prop_label": prop_label, "icon": icon,
                "line": line_data["line"], "over_odds": line_data["over_odds"], "under_odds": line_data["under_odds"],
                "implied_prob": round(abs(line_data["over_odds"]) / (abs(line_data["over_odds"]) + 100), 4),
                "true_lambda": lam, "source": "model_generated", "commence_time": commence,
                "dvoa_label": profile.get("dvoa_label", "average"),
                "script_label": profile.get("script_label", "balanced game"),
            })
    logger.info("Generated " + str(len(props)) + " NFL props")
    return props
