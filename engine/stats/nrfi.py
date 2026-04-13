"""
engine/stats/nrfi.py
NRFI/YRFI model — No Run First Inning / Yes Run First Inning.
Uses both starting pitchers' first inning stats + leadoff hitters.
"""
import requests
import logging
from datetime import datetime
from engine.stats.mlb_stats import get_pitcher_id, get_pitcher_handedness

logger = logging.getLogger(__name__)

MLB_API = "https://statsapi.mlb.com/api/v1"


def _today_str():
    return datetime.now().strftime("%Y-%m-%d")


def get_pitcher_first_inning_stats(player_id: int) -> dict:
    """
    Get pitcher first inning specific stats.
    Uses season game log to calculate first inning ERA and run rate.
    """
    try:
        url = f"{MLB_API}/people/{player_id}/stats"
        params = {
            "stats": "gameLog",
            "group": "pitching",
            "season": datetime.now().year,
            "sportId": 1,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        splits = data.get("stats", [{}])[0].get("splits", [])
        starts = [s for s in splits if int(s.get("stat", {}).get("gamesStarted", 0) or 0) > 0]

        if not starts:
            return _neutral_first_inning()

        # Estimate first inning ERA from season ERA
        # First inning ERA is typically ~20% higher than overall ERA
        season_era = float(starts[-1].get("stat", {}).get("era", 4.50) or 4.50)
        first_inning_era = round(season_era * 1.20, 2)

        # Run rate per inning = ERA / 9
        run_rate_per_inning = round(first_inning_era / 9, 4)

        # Probability of scoring in first inning
        # Using Poisson: P(X>=1) = 1 - e^(-lambda)
        import math
        prob_run = round(1 - math.exp(-run_rate_per_inning), 4)

        logger.info(f"Pitcher {player_id}: 1st inn ERA≈{first_inning_era}, run_rate={run_rate_per_inning}, P(run)={prob_run}")

        return {
            "first_inning_era": first_inning_era,
            "run_rate": run_rate_per_inning,
            "prob_run_allowed": prob_run,
            "starts": len(starts),
        }

    except Exception as e:
        logger.error(f"First inning stats failed for {player_id}: {e}")
        return _neutral_first_inning()


def _neutral_first_inning() -> dict:
    import math
    run_rate = 4.50 * 1.20 / 9
    return {
        "first_inning_era": 5.40,
        "run_rate": run_rate,
        "prob_run_allowed": round(1 - math.exp(-run_rate), 4),
        "starts": 0,
    }


def get_team_leadoff_stats(team_name: str) -> dict:
    """
    Get team's leadoff hitter OBP and power stats.
    Higher OBP = more likely to reach = more likely to score.
    """
    try:
        # Get team roster and find likely leadoff hitter
        url = f"{MLB_API}/teams"
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

        # Get team batting stats as proxy for leadoff quality
        url = f"{MLB_API}/teams/{team_id}/stats"
        params = {"stats": "season", "group": "hitting", "season": datetime.now().year}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        splits = data.get("stats", [{}])[0].get("splits", [])
        if not splits:
            return {"obp": 0.320, "ops": 0.720, "k_pct": 0.22}

        stat = splits[0].get("stat", {})
        obp = float(stat.get("obp", 0.320) or 0.320)
        ops = float(stat.get("ops", 0.720) or 0.720)
        k_pct = float(stat.get("strikeoutPercentage", 0.22) or 0.22)

        logger.info(f"{team_name} batting: OBP={obp}, OPS={ops}, K%={k_pct}")
        return {"obp": obp, "ops": ops, "k_pct": k_pct}

    except Exception as e:
        logger.error(f"Leadoff stats failed for {team_name}: {e}")
        return {"obp": 0.320, "ops": 0.720, "k_pct": 0.22}


def calculate_nrfi_probability(
    home_pitcher: str,
    away_pitcher: str,
    home_team: str,
    away_team: str,
    umpire_adj: float = 1.0,
    weather_adj: float = 1.0,
    park_k_factor: float = 1.0,
) -> dict:
    """
    Calculate NRFI/YRFI probabilities for a game.

    NRFI = neither team scores in the first inning.
    P(NRFI) = P(home pitcher holds) * P(away pitcher holds)

    Returns dict with nrfi_prob, yrfi_prob, edge analysis.
    """
    import math

    logger.info(f"NRFI calc: {away_pitcher} @ {home_pitcher}")

    # Get pitcher IDs
    home_pid = get_pitcher_id(home_pitcher)
    away_pid = get_pitcher_id(away_pitcher)

    # Get first inning stats
    home_stats = get_pitcher_first_inning_stats(home_pid) if home_pid else _neutral_first_inning()
    away_stats = get_pitcher_first_inning_stats(away_pid) if away_pid else _neutral_first_inning()

    # Get offensive stats for each team
    home_offense = get_team_leadoff_stats(home_team)
    away_offense = get_team_leadoff_stats(away_team)

    # Adjust run rates with all factors
    # Away pitcher faces home team offense in bottom of 1st
    home_run_rate = away_stats["run_rate"]
    home_run_rate *= (home_offense["obp"] / 0.320)  # offense adjustment
    home_run_rate *= weather_adj
    home_run_rate *= park_k_factor
    home_run_rate /= umpire_adj  # better umpire zone = fewer runs

    # Home pitcher faces away team offense in top of 1st
    away_run_rate = home_stats["run_rate"]
    away_run_rate *= (away_offense["obp"] / 0.320)
    away_run_rate *= weather_adj
    away_run_rate *= park_k_factor
    away_run_rate /= umpire_adj

    # P(no run scored) = e^(-lambda) for each half inning
    p_home_holds = math.exp(-home_run_rate)  # away pitcher holds home team
    p_away_holds = math.exp(-away_run_rate)  # home pitcher holds away team

    # NRFI = both pitchers hold
    nrfi_prob = round(p_home_holds * p_away_holds, 4)
    yrfi_prob = round(1 - nrfi_prob, 4)

    logger.info(f"NRFI prob={nrfi_prob}, YRFI prob={yrfi_prob}")
    logger.info(f"P(home holds)={round(p_home_holds,4)}, P(away holds)={round(p_away_holds,4)}")

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
    }


def grade_nrfi(nrfi_prob: float, implied_prob: float) -> tuple | None:
    """
    Grade NRFI/YRFI play based on edge vs implied odds.
    Returns (grade, score, label) or None if no edge.
    """
    edge = nrfi_prob - implied_prob

    if edge >= 0.08:
        return "A+", 91, "Sigma Play"
    elif edge >= 0.06:
        return "A", 90, "Precision Play"
    elif edge >= 0.04:
        return "A-", 88, "Sharp Play"
    return None
