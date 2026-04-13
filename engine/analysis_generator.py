import logging
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
LEAGUE_AVG_SWSTR = 0.107
LEAGUE_AVG_K9 = 8.5
LEAGUE_AVG_ERA = 4.25
LEAGUE_AVG_K_PCT = 0.225
 
 
def get_percentile_label(value, avg, higher_is_better=True):
    if higher_is_better:
        ratio = value / avg if avg > 0 else 1.0
    else:
        ratio = avg / value if value > 0 else 1.0
    if ratio >= 1.30:
        return "top 5%"
    elif ratio >= 1.20:
        return "top 10%"
    elif ratio >= 1.12:
        return "top 18%"
    elif ratio >= 1.06:
        return "top 25%"
    elif ratio >= 0.94:
        return "league average"
    elif ratio >= 0.88:
        return "bottom 25%"
    return "bottom 10%"
 
 
def generate_mlb_k_analysis(play):
    try:
        player = play.get("player", "Unknown")
        line = play.get("line", 0)
        true_lambda = play.get("true_lambda", 0)
        edge = play.get("edge", 0)
        grade = play.get("grade", "A")
        team = (play.get("team", "") or "")[:3].upper()
        opp = (play.get("opponent", "") or "")[:3].upper()
        direction = "OVER" if true_lambda > line else "UNDER"
        factors = []
        opp_k_adj = play.get("opp_k_adjustment", 1.0)
        if opp_k_adj >= 1.08:
            opp_k_pct = round(play.get("opp_k_pct", 0.225) * 100, 1)
            factors.append("Opponent K rate: " + str(opp_k_pct) + "% — top strikeout lineup matchup")
        elif opp_k_adj <= 0.92:
            opp_k_pct = round(play.get("opp_k_pct", 0.225) * 100, 1)
            factors.append("Opponent K rate: " + str(opp_k_pct) + "% — contact lineup, fade signal")
        swstr = play.get("swstr_pct", LEAGUE_AVG_SWSTR)
        swstr_label = get_percentile_label(swstr, LEAGUE_AVG_SWSTR)
        if swstr != LEAGUE_AVG_SWSTR:
            factors.append("SwStr% " + str(round(swstr * 100, 1)) + "% — " + swstr_label + " of all starters")
        platoon = play.get("platoon_adjustment", 1.0)
        if platoon >= 1.10:
            factors.append("Platoon edge — lineup vs handedness, K rate +" + str(round((platoon-1)*100)) + "% above avg")
        elif platoon <= 0.92:
            factors.append("Platoon disadvantage — lineup suppresses this pitcher")
        umpire = play.get("umpire_adjustment", 1.0)
        if umpire >= 1.04:
            factors.append("Umpire — +" + str(round((umpire-1)*100)) + "% above avg on called strikes today")
        elif umpire <= 0.96:
            factors.append("Umpire — tight zone, " + str(round((1-umpire)*100)) + "% below avg called strikes")
        k9 = play.get("k9_season", LEAGUE_AVG_K9)
        k9_label = get_percentile_label(k9, LEAGUE_AVG_K9)
        if k9_label in ("top 5%", "top 10%", "top 18%"):
            factors.append("K/9 " + str(round(k9, 1)) + " — " + k9_label + " of all starters")
        if not factors:
            factors.append("Model projects " + str(round(true_lambda, 1)) + " Ks — significant gap vs book line " + str(line))
        top3 = factors[:3]
        lines = ["WHY WE LIKE IT — " + player + " " + direction + " " + str(line) + " K", ""]
        lines.append("The algorithm flagged " + str(len(top3)) + " key signals:")
        lines.append("")
        for i, f in enumerate(top3):
            lines.append(str(i+1) + ". " + f)
        lines += ["", "Model projects: " + str(round(true_lambda, 1)) + " Ks  |  Line: " + str(line) + "  |  Edge: +" + str(round(edge*100, 1)) + "%", "Algorithm confidence: " + grade + " (" + str(play.get("confidence_score", 88)) + ")", "", "No feelings. Just facts.", "#EdgeEquation #MLB #PlayerProps"]
        return "\n".join(lines)
    except Exception as e:
        logger.error("MLB K analysis failed: " + str(e))
        return ""
 
 
def generate_nrfi_analysis(play):
    try:
        player = play.get("player", "")
        pitchers = player.split(" / ")
        home_p = pitchers[1] if len(pitchers) > 1 else "Home Pitcher"
        away_p = pitchers[0]
        prop = play.get("prop_label", "NRFI")
        edge = play.get("edge", 0)
        grade = play.get("grade", "A")
        team = (play.get("team", "") or "")[:3].upper()
        opp = (play.get("opponent", "") or "")[:3].upper()
        home_era = play.get("home_era", 4.25)
        away_era = play.get("away_era", 4.25)
        lines = ["WHY WE LIKE IT — " + prop + " | " + opp + " @ " + team, ""]
        if prop == "NRFI":
            lines += ["Both pitchers show elite first inning profiles:", "", "1. " + away_p + " — blended ERA " + str(round(away_era, 2)), "2. " + home_p + " — blended ERA " + str(round(home_era, 2)), "3. Model: P(scoreless first) = " + str(round(play.get("sim_prob", 0.60)*100, 1)) + "%"]
        else:
            lines += ["First inning run environment elevated:", "", "1. " + away_p + " — blended ERA " + str(round(away_era, 2)), "2. " + home_p + " — blended ERA " + str(round(home_era, 2)), "3. Model: P(first inning run) = " + str(round(play.get("sim_prob", 0.60)*100, 1)) + "%"]
        lines += ["", "Edge: +" + str(round(edge*100, 1)) + "%  |  Grade: " + grade + " (" + str(play.get("confidence_score", 88)) + ")", "", "No feelings. Just facts.", "#EdgeEquation #MLB #" + prop]
        return "\n".join(lines)
    except Exception as e:
        logger.error("NRFI analysis failed: " + str(e))
        return ""
 
 
def generate_nba_analysis(play):
    try:
        player = play.get("player", "")
        line = play.get("line", 0)
        prop = play.get("prop_label", "3PM")
        true_lambda = play.get("true_lambda", 0)
        edge = play.get("edge", 0)
        grade = play.get("grade", "A")
        opp = (play.get("opponent", "") or "")[:3].upper()
        direction = "OVER" if true_lambda > line else "UNDER"
        lines = ["WHY WE LIKE IT — " + player + " " + direction + " " + str(line) + " " + prop, "", "Algorithm signals:", "", "1. Volume — " + str(round(play.get("attempts_per_game", 0), 1)) + " attempts/game (last 10)", "2. Matchup — " + opp + " allows " + str(round(play.get("opp_defense_rate", 0), 1)) + " " + prop + "/game", "3. Pace — " + play.get("pace_label", "above average") + " pace game", "", "Model projects: " + str(round(true_lambda, 1)) + "  |  Line: " + str(line) + "  |  Edge: +" + str(round(edge*100, 1)) + "%", "Grade: " + grade + " (" + str(play.get("confidence_score", 88)) + ")", "", "No feelings. Just facts.", "#EdgeEquation #NBA #PlayerProps"]
        return "\n".join(lines)
    except Exception as e:
        logger.error("NBA analysis failed: " + str(e))
        return ""
 
 
def generate_nhl_analysis(play):
    try:
        player = play.get("player", "")
        line = play.get("line", 0)
        prop = play.get("prop_label", "SOG")
        true_lambda = play.get("true_lambda", 0)
        edge = play.get("edge", 0)
        grade = play.get("grade", "A")
        opp = (play.get("opponent", "") or "")[:3].upper()
        direction = "OVER" if true_lambda > line else "UNDER"
        lines = ["WHY WE LIKE IT — " + player + " " + direction + " " + str(line) + " " + prop, "", "Algorithm signals:", "", "1. Rate — " + str(round(play.get("sog_per_60", 0), 1)) + " SOG/60 min (blended)", "2. Ice time — " + str(round(play.get("avg_toi", 0), 1)) + " min projected", "3. Opponent — " + opp + " allows " + str(round(play.get("opp_sog_allowed", 0), 1)) + " SOG/game", "", "Model projects: " + str(round(true_lambda, 1)) + " SOG  |  Line: " + str(line) + "  |  Edge: +" + str(round(edge*100, 1)) + "%", "Grade: " + grade + " (" + str(play.get("confidence_score", 88)) + ")", "", "No feelings. Just facts.", "#EdgeEquation #NHL #PlayerProps"]
        return "\n".join(lines)
    except Exception as e:
        logger.error("NHL analysis failed: " + str(e))
        return ""
 
 
def generate_nfl_analysis(play):
    try:
        player = play.get("player", "")
        line = play.get("line", 0)
        prop = play.get("prop_label", "PassYds")
        true_lambda = play.get("true_lambda", 0)
        edge = play.get("edge", 0)
        grade = play.get("grade", "A")
        opp = (play.get("opponent", "") or "")[:3].upper()
        direction = "OVER" if true_lambda > line else "UNDER"
        lines = ["WHY WE LIKE IT — " + player + " " + direction + " " + str(line) + " " + prop, "", "Algorithm signals:", "", "1. Implied total — game total projects high passing volume", "2. Opponent DVOA — " + opp + " defense rated " + play.get("dvoa_label", "below average"), "3. Game script — " + play.get("script_label", "balanced game"), "", "Model projects: " + str(round(true_lambda, 1)) + "  |  Line: " + str(line) + "  |  Edge: +" + str(round(edge*100, 1)) + "%", "Grade: " + grade + " (" + str(play.get("confidence_score", 88)) + ")", "", "No feelings. Just facts.", "#EdgeEquation #NFL #PlayerProps"]
        return "\n".join(lines)
    except Exception as e:
        logger.error("NFL analysis failed: " + str(e))
        return ""
 
 
def generate_why_we_passed(notable_games):
    if not notable_games:
        return ""
    try:
        game = notable_games[0]
        player = game.get("player", "")
        line = game.get("line", 0)
        prop = game.get("prop_label", "K")
        true_lambda = game.get("true_lambda", 0)
        implied_prob = game.get("implied_prob", 0.524)
        reasons = game.get("pass_reasons", [])
        lines = ["WHY WE PASSED — " + player + " " + str(line) + " " + prop, "", "Everyone is on this today. Here is why the algorithm passed:", ""]
        for i, r in enumerate(reasons[:3]):
            lines.append(str(i+1) + ". " + r)
        lines += ["", "Model projects: " + str(round(true_lambda, 1)) + " — not enough edge at " + str(round(implied_prob*100, 1)) + "% implied", "", "We see the same game. The math just does not support it.", "No feelings. Just facts.", "#EdgeEquation"]
        return "\n".join(lines)
    except Exception as e:
        logger.error("Why we passed failed: " + str(e))
        return ""
 
 
def generate_analysis(play):
    sport = play.get("sport", "")
    prop = play.get("prop_label", "")
    if prop in ("NRFI", "YRFI"):
        return generate_nrfi_analysis(play)
    elif sport == "baseball_mlb":
        return generate_mlb_k_analysis(play)
    elif sport == "basketball_nba":
        return generate_nba_analysis(play)
    elif sport == "icehockey_nhl":
        return generate_nhl_analysis(play)
    elif sport == "americanfootball_nfl":
        return generate_nfl_analysis(play)
    return ""
 
 
def generate_all_analysis(plays, notable_passed=None):
    analyses = []
    for play in plays:
        text = generate_analysis(play)
        if text:
            analyses.append({"play": play, "text": text})
    why_passed = ""
    if notable_passed:
        why_passed = generate_why_we_passed(notable_passed)
     return analyses, why_passed
