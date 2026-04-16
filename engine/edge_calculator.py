import numpy as np
import logging
from config.settings import MC_SIMULATIONS, GRADE_THRESHOLDS, NRFI_IMPLIED, YRFI_IMPLIED

logger = logging.getLogger(__name__)


# ============================================================
# BASIC HELPERS
# ============================================================

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


# ============================================================
# TRUE LAMBDA — MLB PITCHERS
# ============================================================

def calculate_true_lambda_mlb(prop):
    try:
        from engine.stats.mlb_stats import get_full_pitcher_profile
        from engine.stats.weather import get_weather
        from engine.stats.umpire import get_umpire_for_game
        from engine.stats.park_factors import get_k_factor, get_altitude_adjustment
        from engine.stats.savant import (
            get_blended_savant_stats,
            get_swstr_k_adjustment,
            get_pitch_mix_adjustment
        )

        player = prop.get("player", "")
        home_team = prop.get("team", "")
        away_team = prop.get("opponent", "")

        profile = get_full_pitcher_profile(player, away_team, home_team)

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

        logger.info(
            f"True lambda={round(true_lambda,3)} "
            f"(opp={opp_adj} platoon={platoon_adj} wx={weather_adj} "
            f"ump={umpire_adj} park={park_adj} swstr={swstr_adj})"
        )

        return round(true_lambda, 3)

    except Exception as e:
        logger.error("True lambda failed: " + str(e))
        return max(prop.get("true_lambda", prop.get("line", 5.0)), 0.1)


# ============================================================
# TRUE LAMBDA — MLB BATTERS
# ============================================================

def calculate_true_lambda_batter(prop):
    """
    Generic batter lambda for counting stats:
    HITS, TOTAL_BASES, HOME_RUNS, RBI, RUNS, etc.
    """
    try:
        from engine.stats.mlb_batter import get_full_batter_profile
        from engine.stats.weather import get_weather
        from engine.stats.park_factors import get_batter_park_adjustment
        from engine.stats.pitcher_matchup import get_pitcher_matchup_adjustment

        player = prop.get("player", "")
        team = prop.get("team", "")
        opponent = prop.get("opponent", "")
        prop_label = prop.get("prop_label", "HITS")

        profile = get_full_batter_profile(player, team, opponent)

        # Base per-game expectation by prop type
        if prop_label == "HITS":
            base = profile.get("hits_per_game", 1.0)
        elif prop_label == "TOTAL_BASES":
            base = profile.get("tb_per_game", 2.0)
        elif prop_label == "HOME_RUNS":
            base = profile.get("hr_per_game", 0.25)
        elif prop_label == "RBI":
            base = profile.get("rbi_per_game", 0.8)
        elif prop_label == "RUNS":
            base = profile.get("runs_per_game", 0.8)
        else:
            base = profile.get("stat_per_game", 1.0)

        pitcher_adj = get_pitcher_matchup_adjustment(profile)
        park_adj = get_batter_park_adjustment(team, prop_label)

        weather = get_weather(team)
        weather_adj = weather.get("run_env_adjustment", 1.0)

        true_lambda = base * pitcher_adj * park_adj * weather_adj

        logger.info(
            f"True lambda batter={player} prop={prop_label} "
            f"lambda={round(true_lambda,3)} "
            f"(base={round(base,3)} pitch={pitcher_adj} "
            f"park={park_adj} wx={weather_adj})"
        )

        return round(max(true_lambda, 0.05), 3)

    except Exception as e:
        logger.error("True lambda batter failed: " + str(e))
        return max(prop.get("true_lambda", prop.get("line", 1.0)), 0.05)


# ============================================================
# NRFI / YRFI ENGINE
# ============================================================

def calculate_nrfi_plays():
    try:
        from engine.nrfi_model import get_nrfi_probabilities
        plays = get_nrfi_probabilities() or []

        for p in plays:
            implied = NRFI_IMPLIED if p.get("prop_label") == "NRFI" else YRFI_IMPLIED
            p["edge"] = round(p.get("prob", 0) - implied, 4)

        return plays

    except Exception as e:
        logger.error("NRFI engine failed: " + str(e))
        return []


# ============================================================
# PROP GRADING ENGINE
# ============================================================

def grade_all_props(props):
    graded = []

    for prop in props:
        try:
            line = prop.get("line", 0)
            prop_label = prop.get("prop_label", "")

            # Select lambda engine
            if prop_label == "K":
                lam = calculate_true_lambda_mlb(prop)
            else:
                lam = calculate_true_lambda_batter(prop)

            prob = run_monte_carlo(lam, line)
            edge = round(prob - prop.get("implied_prob", 0), 4)

            grade_info = assign_grade(edge)
            if grade_info:
                grade, score, label = grade_info
            else:
                grade, score, label = None, None, None

            graded.append({
                **prop,
                "true_lambda": lam,
                "prob": prob,
                "edge": edge,
                "grade": grade,
                "score": score,
                "label": label,
            })

        except Exception as e:
            logger.error("Prop grading failed: " + str(e))

    return graded
