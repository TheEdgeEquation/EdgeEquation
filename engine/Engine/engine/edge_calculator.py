"""
engine/edge_calculator.py
Runs 10,000 Poisson Monte Carlo simulations per prop.
Calculates over-probability, edge vs. implied odds, and assigns A+/A/A- grade.
"""
import numpy as np
import logging
from config.settings import MC_SIMULATIONS, GRADE_THRESHOLDS

logger = logging.getLogger(__name__)


def poisson_lambda_from_line(line: float) -> float:
    return max(line, 0.1)


def run_monte_carlo(line: float, lam: float | None = None) -> float:
    if lam is None:
        lam = poisson_lambda_from_line(line)
    rng = np.random.default_rng()
    draws = rng.poisson(lam=lam, size=MC_SIMULATIONS)
    over_hits = np.sum(draws > line)
    return round(float(over_hits) / MC_SIMULATIONS, 4)


def assign_grade(edge: float) -> tuple[str, int, str] | None:
    for grade, threshold, score, label in GRADE_THRESHOLDS:
        if edge >= threshold:
            return grade, score, label
    return None


def calculate_edge(prop: dict) -> dict | None:
    line = prop.get("line", 0.0)
    implied_prob = prop.get("implied_prob", 0.5)

    sim_prob = run_monte_carlo(line)
    edge = round(sim_prob - implied_prob, 4)

    grade_result = assign_grade(edge)
    if grade_result is None:
        return None

    grade, score, play_label = grade_result

    return {
        **prop,
        "sim_prob": sim_prob,
        "edge": edge,
        "grade": grade,
        "confidence_score": score,
        "play_label": play_label,
        "display_line": f"OVER {line}",
        "display_odds": _format_odds(prop.get("over_odds", -110)),
    }


def _format_odds(odds: int) -> str:
    return f"+{odds}" if odds > 0 else str(odds)


def grade_all_props(props: list[dict]) -> list[dict]:
    graded = []
    for prop in props:
        result = calculate_edge(prop)
        if result:
            graded.append(result)

    grade_order = {"A+": 0, "A": 1, "A-": 2}
    graded.sort(key=lambda x: (grade_order.get(x["grade"], 9), -x["edge"]))

    logger.info(f"Graded plays: {len(graded)} of {len(props)} props passed threshold")
    return graded
