import numpy as np
import logging
from config.settings import MC_SIMULATIONS, GRADE_THRESHOLDS, NRFI_IMPLIED, YRFI_IMPLIED
 
logger = logging.getLogger(__name__)
 
 
def _format_odds(odds):
    return "+" + str(odds) if odds > 0 else str(odds)
 
 
def run_monte_carlo(lam, line):
    rng = np.random.default_rng()
    draws = rng.poisson(lam=max(lam, 0.1), size=MC_SIMULATIONS)
    over_hits = np.sum(draws > line)
    return round(float(over_hits) / MC_SIMULATIONS, 4)
 
 
def assign_grade(edge):
    for grade, threshold, score, label in GRADE_THRESHOLDS:
        if edge >= threshold:
            return grade, score, label
    return None
 
 
def calculate_true_lambda_mlb(prop):
    try:
        from engine.stats.mlb_stats import get_full_pitcher_profile
        from engine.stats.weather import get_weather
        from engine.stats.umpire import get_umpire_for_game
        from engine.stats.park_factors import get_k_factor, get_altitude_adjustment
        from engine.stats.savant import get_blended_savant_stats, get_swstr_k_adjustment, get_pitch_mix_adjustment
 
        player = prop.get("player", "")
        home_team = prop.get("team", "")
        away_team = prop.get("opponent", "")
 
        profile = get_full_pitcher_profile(player, away_team, home_team)
        k9_season = profile.get("k9_season", 8.0)
        k9_recent = profile.get("k9_recent", k9_season)
        avg_ip = profile.get("avg_ip_recent", 5.5)
        k9_blended = (k9_recent * 0.60) + (k9_season * 0.40)
        base_lambda = (k9_blended / 9.0) * avg_ip
        logger.info(player + ": K9=" + str(round(k9_blended,2)) + " IP=" + str(avg_ip) + " base=" + str(round(base_lambda,2)))
 
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
            logger.info(player + " SwStr=" + str(savant.get("swstr_pct")) + " adj=" + str(swstr_adj) + " pitchmix=" + str(pitch_mix_adj))
 
        true_lambda = (
            base_lambda
            * opp_adj
            * platoon_adj
            * weather_adj
            * umpire_adj
            * park_adj
            * alt_adj
            * swstr_adj
            * pitch_mix_adj
        )
        logger.info("True lambda=" + str(round(true_lambda,3)) + " (opp=" + str(opp_adj) + " platoon=" + str(platoon_adj) + " wx=" + str(weather_adj) + " ump=" + str(umpire_adj) + " park=" + str(park_adj) + " swstr=" + str(swstr_adj) + ")")
        return round(true_lambda, 3)
 
    except Exception as e:
        logger.error("True lambda failed: " + str(e))
        return max(prop.get("line", 5.0), 0.1)
 
 
def calculate_edge(prop):
    sport = prop.get("sport", "")
    line = prop.get("line", 0.0)
    implied_prob = prop.get("implied_prob", 0.5)
    if sport == "baseball_mlb":
        lam = calculate_true_lambda_mlb(prop)
    else:
        lam = max(line, 0.1)
    sim_prob = run_monte_carlo(lam, line)
    edge = round(sim_prob - implied_prob, 4)
    grade_result = assign_grade(edge)
    if grade_result is None:
        return None
    grade, score, play_label = grade_result
    return {
        **prop,
        "true_lambda": lam,
        "sim_prob": sim_prob,
        "edge": edge,
        "grade": grade,
        "confidence_score": score,
        "play_label": play_label,
        "display_line": "OVER " + str(line),
        "display_odds": _format_odds(prop.get("over_odds", -110)),
    }
 
 
def calculate_nrfi_plays(style="ee"):
    try:
        from engine.stats.nrfi import calculate_nrfi_probability, grade_nrfi
        from engine.stats.weather import get_weather
        from engine.stats.umpire import get_umpire_for_game
        from engine.stats.park_factors import get_k_factor, is_dome
        from engine.stats.odds_nrfi import get_nrfi_lines, get_nrfi_implied_for_game
        import requests
        from datetime import datetime
 
        logger.info("Fetching todays MLB games for NRFI/YRFI...")
        url = "https://statsapi.mlb.com/api/v1/schedule"
        params = {"sportId": 1, "hydrate": "probablePitcher,team", "date": datetime.now().strftime("%Y-%m-%d")}
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
 
        nrfi_lines = get_nrfi_lines()
        nrfi_plays = []
 
        for date in data.get("dates", []):
            for game in date.get("games", []):
                try:
                    home = game.get("teams", {}).get("home", {})
                    away = game.get("teams", {}).get("away", {})
                    home_team = home.get("team", {}).get("name", "")
                    away_team = away.get("team", {}).get("name", "")
                    home_pitcher = home.get("probablePitcher", {}).get("fullName", "")
                    away_pitcher = away.get("probablePitcher", {}).get("fullName", "")
                    if not home_pitcher or not away_pitcher:
                        logger.warning("Missing pitcher for " + away_team + " @ " + home_team)
                        continue
                    logger.info("NRFI: " + away_pitcher + " @ " + home_pitcher)
                    weather = get_weather(home_team)
                    weather_adj = weather.get("k_adjustment", 1.0)
                    umpire_name, umpire_adj = get_umpire_for_game(home_team, away_team)
                    park_factor = get_k_factor(home_team)
                    nrfi_implied, yrfi_implied, nrfi_odds, yrfi_odds = get_nrfi_implied_for_game(home_team, away_team, nrfi_lines)
                    result = calculate_nrfi_probability(
                        home_pitcher=home_pitcher,
                        away_pitcher=away_pitcher,
                        home_team=home_team,
                        away_team=away_team,
                        umpire_adj=umpire_adj,
                        weather_adj=weather_adj,
                        park_k_factor=park_factor,
                    )
                    if result is None:
                        continue
                    nrfi_prob = result["nrfi_prob"]
                    yrfi_prob = result["yrfi_prob"]
                    both_elite = result.get("both_elite", False)
                    commence = game.get("gameDate", "")
                    nrfi_edge = round(nrfi_prob - nrfi_implied, 4)
                    yrfi_edge = round(yrfi_prob - yrfi_implied, 4)
                    nrfi_grade = grade_nrfi(nrfi_prob, nrfi_implied, both_elite)
                    yrfi_grade = grade_nrfi(yrfi_prob, yrfi_implied, both_elite)
                    if nrfi_grade:
                        grade, score, label = nrfi_grade
                        nrfi_plays.append({"player": away_pitcher + " / " + home_pitcher, "team": home_team, "opponent": away_team, "sport": "baseball_mlb", "sport_label": "MLB", "prop_label": "NRFI", "icon": "⚾", "line": 0.5, "over_odds": nrfi_odds, "under_odds": yrfi_odds, "implied_prob": nrfi_implied, "sim_prob": nrfi_prob, "edge": nrfi_edge, "grade": grade, "confidence_score": score, "play_label": label, "display_line": "NRFI", "display_odds": _format_odds(nrfi_odds), "true_lambda": nrfi_prob, "commence_time": commence, "umpire": umpire_name, "weather": weather.get("condition", ""), "dome": is_dome(home_team)})
                        logger.info("NRFI: " + away_team + " @ " + home_team + " " + grade + " edge=" + str(nrfi_edge))
                    if yrfi_grade:
                        grade, score, label = yrfi_grade
                        nrfi_plays.append({"player": away_pitcher + " / " + home_pitcher, "team": home_team, "opponent": away_team, "sport": "baseball_mlb", "sport_label": "MLB", "prop_label": "YRFI", "icon": "⚾", "line": 0.5, "over_odds": yrfi_odds, "under_odds": nrfi_odds, "implied_prob": yrfi_implied, "sim_prob": yrfi_prob, "edge": yrfi_edge, "grade": grade, "confidence_score": score, "play_label": label, "display_line": "YRFI", "display_odds": _format_odds(yrfi_odds), "true_lambda": yrfi_prob, "commence_time": commence, "umpire": umpire_name, "weather": weather.get("condition", ""), "dome": is_dome(home_team)})
                        logger.info("YRFI: " + away_team + " @ " + home_team + " " + grade + " edge=" + str(yrfi_edge))
                except Exception as e:
                    logger.error("NRFI calc failed: " + str(e))
                    continue
        logger.info("NRFI/YRFI: " + str(len(nrfi_plays)) + " plays found")
        return nrfi_plays
    except Exception as e:
        logger.error("NRFI pipeline failed: " + str(e))
        return []
 
 
def grade_all_props(props):
    graded = []
    for prop in props:
        result = calculate_edge(prop)
        if result:
            graded.append(result)
    grade_order = {"A+": 0, "A": 1, "A-": 2}
    graded.sort(key=lambda x: (grade_order.get(x["grade"], 9), -x["edge"]))
    logger.info("Graded: " + str(len(graded)) + " of " + str(len(props)) + " passed")
    return graded
