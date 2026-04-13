"""
engine/edge_calculator.py
Sharp MLB strikeout model using real stats, weather, umpire, and park factors.
Runs 10,000 Poisson Monte Carlo simulations using TRUE lambda from real data.
"""
import numpy as np
import logging
from config.settings import MC_SIMULATIONS, GRADE_THRESHOLDS

logger = logging.getLogger(__name__)


def _format_odds(odds: int) -> str:
    return f"+{odds}" if odds > 0 else str(odds)


def run_monte_carlo(lam: float, line: float) -> float:
    """Run MC_SIMULATIONS Poisson draws. Returns P(result > line)."""
    rng = np.random.default_rng()
    draws = rng.poisson(lam=max(lam, 0.1), size=MC_SIMULATIONS)
    over_hits = np.sum(draws > line)
    return round(float(over_hits) / MC_SIMULATIONS, 4)


def assign_grade(edge: float) -> tuple | None:
    for grade, threshold, score, label in GRADE_THRESHOLDS:
        if edge >= threshold:
            return grade, score, label
    return None


def calculate_true_lambda_mlb(prop: dict) -> float:
    """
    Calculate true expected strikeout total using real pitcher stats,
    opponent K rate, weather, umpire, and park factors.
    This is the core of the sharp model.
    """
    try:
        from engine.stats.mlb_stats import get_full_pitcher_profile
        from engine.stats.weather import get_weather
        from engine.stats.umpire import get_umpire_for_game
        from engine.stats.park_factors import get_k_factor, get_altitude_adjustment

        player = prop.get("player", "")
        home_team = prop.get("team", "")
        away_team = prop.get("opponent", "")

        # Get full pitcher profile
        profile = get_full_pitcher_profile(player, away_team, home_team)

        # Base lambda — weighted blend of season and recent K/9
        # Recent form weighted 60%, season 40%
        k9_season = profile.get("k9_season", 8.0)
        k9_recent = profile.get("k9_recent", k9_season)
        avg_ip = profile.get("avg_ip_recent", 5.5)

        k9_blended = (k9_recent * 0.60) + (k9_season * 0.40)

        # Base expected Ks = K/9 rate * projected innings
        base_lambda = (k9_blended / 9.0) * avg_ip
        logger.info(f"{player}: K/9={k9_blended:.2f}, IP={avg_ip}, base_lambda={base_lambda:.2f}")

        # Opponent adjustment
        opp_adj = profile.get("opp_k_adjustment", 1.0)
        logger.info(f"Opponent K adj: {opp_adj}")

        # Weather adjustment
        weather = get_weather(home_team)
        weather_adj = weather.get("k_adjustment", 1.0)
        logger.info(f"Weather adj: {weather_adj}")

        # Umpire adjustment
        umpire_name, umpire_adj = get_umpire_for_game(home_team, away_team)
        logger.info(f"Umpire: {umpire_name}, adj={umpire_adj}")

        # Park factor
        park_adj = get_k_factor(home_team)
        altitude_adj = get_altitude_adjustment(home_team)
        logger.info(f"Park adj: {park_adj}, altitude adj: {altitude_adj}")

        # True lambda
        true_lambda = (
            base_lambda
            * opp_adj
            * weather_adj
            * umpire_adj
            * park_adj
            * altitude_adj
        )

        logger.info(f"True lambda for {player}: {true_lambda:.3f}")
        return round(true_lambda, 3)

    except Exception as e:
        logger.error(f"True lambda calculation failed: {e} — falling back to line-based")
        return max(prop.get("line", 5.0), 0.1)


def calculate_edge(prop: dict) -> dict | None:
    """
    Calculate edge for a single prop.
    Uses true lambda for MLB strikeouts, line-based for other sports.
    """
    sport = prop.get("sport", "")
    line = prop.get("line", 0.0)
    implied_prob = prop.get("implied_prob", 0.5)

    # Use sharp model for MLB strikeouts
    if sport == "baseball_mlb":
        lam = calculate_true_lambda_mlb(prop)
    else:
        # Other sports — still use line as lambda (to be improved per sport)
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
        "display_line": f"OVER {line}",
        "display_odds": _format_odds(prop.get("over_odds", -110)),
    }


def grade_all_props(props: list[dict]) -> list[dict]:
    """Grade all props. Returns only A+/A/A- plays sorted best first."""
    graded = []
    for prop in props:
        result = calculate_edge(prop)
        if result:
            graded.append(result)

    grade_order = {"A+": 0, "A": 1, "A-": 2}
    graded.sort(key=lambda x: (grade_order.get(x["grade"], 9), -x["edge"]))

    logger.info(f"Graded: {len(graded)} of {len(props)} props passed threshold")
    return graded
