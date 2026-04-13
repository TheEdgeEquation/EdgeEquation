import requests
import logging
import math
from datetime import datetime
from engine.stats.mlb_stats import get_pitcher_id
 
logger = logging.getLogger(__name__)
 
MLB_API = "https://statsapi.mlb.com/api/v1"
MIN_STARTS_REQUIRED = 0
MAX_NRFI_PLAYS = 3
 
 
def _today_str():
    return datetime.now().strftime("%Y-%m-%d")
 
 
def get_pitcher_first_inning_stats(player_id):
    if not player_id:
        return _insufficient_data()
    try:
        from engine.stats.mlb_stats import get_pitcher_season_stats, get_season_weight
        current_year = datetime.now().year
        last_year = current_year - 1
        url = MLB_API + "/people/" + str(player_id) + "/stats"
        params = {"stats": "gameLog", "group": "pitching", "season": current_year, "sportId": 1}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        splits = data.get("stats", [{}])[0].get("splits", [])
        starts = [s for s in splits if int(s.get("stat", {}).get("gamesStarted", 0) or 0) > 0]
        current_starts = len(starts)
        cw, lw = get_season_weight(current_starts)
        logger.info("Pitcher " + str(player_id) + ": " + str(current_starts) + " starts cw=" + str(cw) + " lw=" + str(lw))
        last_season = get_pitcher_season_stats(player_id, last_year)
        last_era = last_season.get("era", 4.50) if last_season else 4.50
        if current_starts >= 2:
            recent = starts[-5:] if len(starts) >= 5 else starts
            total_weight = 0
            weighted_era_sum = 0.0
            for i, start in enumerate(recent):
                weight = i + 1
                era = float(start.get("stat", {}).get("era", 4.50) or 4.50)
                weighted_era_sum += era * weight
                total_weight += weight
            current_era = weighted_era_sum / total_weight if total_weight > 0 else 4.50
        else:
            current_era = last_era
            cw, lw = 0.0, 1.0
        blended_era = round((current_era * cw) + (last_era * lw), 3)
        first_inning_era = round(blended_era * 1.18, 2)
        run_rate = round(first_inning_era / 9, 4)
        prob_run = round(1 - math.exp(-run_rate), 4)
        logger.info("Pitcher " + str(player_id) + ": blended=" + str(blended_era) + " 1stERA=" + str(first_inning_era) + " P(run)=" + str(prob_run))
        return {
            "first_inning_era": first_inning_era,
            "run_rate": run_rate,
            "prob_run_allowed": prob_run,
            "starts": current_starts,
            "sufficient_data": True,
            "weighted_era": blended_era,
        }
    except Exception as e:
        logger.error("First inning stats failed for " + str(player_id) + ": " + str(e))
        return _neutral_first_inning()
 
 
def _neutral_first_inning():
    run_rate = 4.50 * 1.18 / 9
    return {
        "first_inning_era": 5.31,
        "run_rate": run_rate,
        "prob_run_allowed": round(1 - math.exp(-run_rate), 4),
        "starts": 0,
        "sufficient_data": True,
        "weighted_era": 4.50,
    }
 
 
def _insufficient_data():
    return {
        "first_inning_era": None,
        "run_rate": None,
        "prob_run_allowed": None,
        "starts": 0,
        "sufficient_data": False,
        "weighted_era": None,
    }
 
 
def get_team_leadoff_stats(team_name):
    try:
        url = MLB_API + "/teams"
        params = {"sportId": 1, "season": datetime.now().year}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        teams = resp.json().get("teams", [])
        team_id = None
        for t in teams:
            if team_name.lower() in t.get("name", "").lower():
                team_id = t["id"]
                break
        if not team_id:
            return {"obp": 0.320, "ops": 0.720, "k_pct": 0.22}
        url = MLB_API + "/teams/" + str(team_id) + "/stats"
        params = {"stats": "season", "group": "hitting", "season": datetime.now().year}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        splits = data.get("stats", [{}])[0].get("splits", [])
        if not splits:
            return {"obp": 0.320, "ops": 0.720, "k_pct": 0.22}
        stat = splits[0].get("stat", {})
        return {
            "obp": float(stat.get("obp", 0.320) or 0.320),
            "ops": float(stat.get("ops", 0.720) or 0.720),
            "k_pct": float(stat.get("strikeoutPercentage", 0.22) or 0.22),
        }
    except Exception as e:
        logger.error("Leadoff stats failed: " + str(e))
        return {"obp": 0.320, "ops": 0.720, "k_pct": 0.22}
 
 
def calculate_nrfi_probability(home_pitcher, away_pitcher, home_team, away_team, umpire_adj=1.0, weather_adj=1.0, park_k_factor=1.0):
    logger.info("NRFI: " + away_pitcher + " @ " + home_pitcher)
    home_pid = get_pitcher_id(home_pitcher)
    away_pid = get_pitcher_id(away_pitcher)
    home_stats = get_pitcher_first_inning_stats(home_pid)
    away_stats = get_pitcher_first_inning_stats(away_pid)
    if not home_stats["sufficient_data"] or not away_stats["sufficient_data"]:
        logger.warning("Insufficient data - skipping " + home_pitcher + " / " + away_pitcher)
        return None
    home_offense = get_team_leadoff_stats(home_team)
    away_offense = get_team_leadoff_stats(away_team)
    home_run_rate = away_stats["run_rate"]
    home_run_rate *= (home_offense["obp"] / 0.320)
    home_run_rate *= weather_adj
    home_run_rate *= park_k_factor
    home_run_rate /= umpire_adj
    away_run_rate = home_stats["run_rate"]
    away_run_rate *= (away_offense["obp"] / 0.320)
    away_run_rate *= weather_adj
    away_run_rate *= park_k_factor
    away_run_rate /= umpire_adj
    home_elite = home_stats.get("weighted_era", 4.50) < 3.20
    away_elite = away_stats.get("weighted_era", 4.50) < 3.20
    both_elite = home_elite and away_elite
    one_elite = home_elite or away_elite
    p_home_holds = math.exp(-home_run_rate)
    p_away_holds = math.exp(-away_run_rate)
    nrfi_prob = round(p_home_holds * p_away_holds, 4)
    yrfi_prob = round(1 - nrfi_prob, 4)
    logger.info("NRFI=" + str(nrfi_prob) + " YRFI=" + str(yrfi_prob) + " both_elite=" + str(both_elite) + " one_elite=" + str(one_elite))
    return {
        "nrfi_prob": nrfi_prob,
        "yrfi_prob": yrfi_prob,
        "p_home_holds": round(p_home_holds, 4),
        "p_away_holds": round(p_away_holds, 4),
        "home_run_rate": round(home_run_rate, 4),
        "away_run_rate": round(away_run_rate, 4),
        "home_pitcher": home_pitcher,
        "away_pitcher": away_pitcher,
        "home_team": home_team,
        "away_team": away_team,
        "both_elite": both_elite,
        "one_elite": one_elite,
        "neither_elite": not one_elite,
        "home_era": home_stats.get("weighted_era", 4.50),
        "away_era": away_stats.get("weighted_era", 4.50),
    }
 
 
def grade_nrfi(nrfi_prob, implied_prob, both_elite=False, one_elite=False, neither_elite=False):
    edge = nrfi_prob - implied_prob
 
    if neither_elite:
        return None
 
    if both_elite:
        if edge >= 0.12:
            return "A+", 91, "Sigma Play"
        elif edge >= 0.10:
            return "A", 90, "Precision Play"
        elif edge >= 0.08:
            return "A-", 88, "Sharp Play"
 
    elif one_elite:
        if edge >= 0.16:
            return "A+", 91, "Sigma Play"
        elif edge >= 0.13:
            return "A", 90, "Precision Play"
        elif edge >= 0.10:
            return "A-", 88, "Sharp Play"
 
    return None
