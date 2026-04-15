import math
from dataclasses import dataclass
from typing import Dict, Optional, List, Literal

Sport = Literal["nba", "nhl"]


# =========================
# DATA STRUCTURES
# =========================

@dataclass
class SeriesProjection:
    sport: Sport
    higher_seed: str
    lower_seed: str
    conference: str
    projected_winner: str
    win_probability: float
    most_likely_result: str
    series_probs: Dict[str, float]
    model_series_win_pct: float
    expert_series_win_pct: float
    blurb: str


# =========================
# TEAM STRENGTH + EXPERT DATA
# (FILL THESE WITH YOUR REAL NUMBERS)
# =========================

TEAM_STRENGTH: Dict[tuple, float] = {
    # Examples — replace with your ratings
    ("nba", "Boston Celtics"): 7.8,
    ("nba", "Orlando Magic"): 2.1,
    ("nba", "New York Knicks"): 4.3,
    ("nba", "Detroit Pistons"): -3.2,
    ("nhl", "Dallas Stars"): 6.4,
    ("nhl", "Colorado Avalanche"): 5.1,
    ("nhl", "Toronto Maple Leafs"): 4.9,
    ("nhl", "Ottawa Senators"): 1.2,
}

EXPERT_SERIES_PROB: Dict[tuple, float] = {
    # Probability the HIGHER seed wins (0–1)
    ("nba", "Boston Celtics", "Orlando Magic"): 0.84,
    ("nhl", "Dallas Stars", "Colorado Avalanche"): 0.61,
}


def get_team_strength(team: str, sport: Sport) -> float:
    return TEAM_STRENGTH.get((sport, team), 0.0)


def get_expert_series_prob(higher: str, lower: str, sport: Sport) -> Optional[float]:
    return EXPERT_SERIES_PROB.get((sport, higher, lower))


# =========================
# CORE MATH
# =========================

def win_prob_from_strength(higher_strength: float, lower_strength: float) -> float:
    diff = higher_strength - lower_strength
    p = 1 / (1 + math.exp(-diff / 2.0))  # logistic transform
    return max(0.05, min(0.95, p))


def series_distribution_best_of_7(higher_win_pct: float) -> Dict[str, float]:
    lower_win_pct = 1 - higher_win_pct
    dist: Dict[str, float] = {}

    for games in range(4, 8):
        # Higher wins in X games
        prob_high = math.comb(games - 1, 3) * (higher_win_pct ** 4) * (lower_win_pct ** (games - 4))
        dist[f"{games} games - higher"] = round(prob_high * 100, 1)

        # Lower wins in X games
        prob_low = math.comb(games - 1, 3) * (lower_win_pct ** 4) * (higher_win_pct ** (games - 4))
        dist[f"{games} games - lower"] = round(prob_low * 100, 1)

    return dist


def aggregate_series_win_pct(dist: Dict[str, float]):
    higher = sum(v for k, v in dist.items() if "higher" in k)
    lower = sum(v for k, v in dist.items() if "lower" in k)
    return round(higher, 1), round(lower, 1)


def hybrid_series_win_pct(model_pct: float, expert_pct: Optional[float], weight: float = 0.7) -> float:
    if expert_pct is None:
        return model_pct
    return round(weight * model_pct + (1 - weight) * (expert_pct * 100), 1)


# =========================
# BLURB GENERATION
# =========================

def generate_blurb(
    sport: Sport,
    higher: str,
    lower: str,
    higher_strength: float,
    lower_strength: float,
    model_pct: float,
    expert_pct: Optional[float],
    final_pct: float,
) -> str:
    diff = higher_strength - lower_strength
    leader = higher if final_pct >= 50 else lower

    if sport == "nba":
        base = f"{leader} grades out stronger in efficiency and possession quality."
    else:
        base = f"{leader} holds the edge in shot quality and chance generation."

    if abs(diff) < 1:
        comp = "The gap is small, so the series projects as competitive."
    elif abs(diff) < 3:
        comp = "There is a clear but not overwhelming edge in the underlying numbers."
    else:
        comp = "The underlying numbers show a decisive advantage."

    if expert_pct is None:
        expert_line = "The projection is driven entirely by the model."
    else:
        expert_line = (
            f"The final probability blends the model ({model_pct}%) "
            f"with external expectations ({expert_pct * 100:.1f}%)."
        )

    return f"{base} {comp} {expert_line}"


# =========================
# MAIN SERIES ENGINE
# =========================

def project_series(
    higher_seed: str,
    lower_seed: str,
    conference: str,
    sport: Sport,
) -> SeriesProjection:
    higher_strength = get_team_strength(higher_seed, sport)
    lower_strength = get_team_strength(lower_seed, sport)

    higher_win_pct_game = win_prob_from_strength(higher_strength, lower_strength)

    dist = series_distribution_best_of_7(higher_win_pct_game)
    model_higher_pct, model_lower_pct = aggregate_series_win_pct(dist)

    expert_pct = get_expert_series_prob(higher_seed, lower_seed, sport)
    final_higher_pct = hybrid_series_win_pct(model_higher_pct, expert_pct)

    if final_higher_pct >= 50:
        winner = higher_seed
        win_pct = final_higher_pct
    else:
        winner = lower_seed
        win_pct = round(100 - final_higher_pct, 1)

    most_likely_key = max(dist, key=dist.get)
    games, side = most_likely_key.split(" games - ")
    ml_winner = higher_seed if side == "higher" else lower_seed
    ml_result = f"{games} games - {ml_winner}"

    blurb = generate_blurb(
        sport,
        higher_seed,
        lower_seed,
        higher_strength,
        lower_strength,
        model_higher_pct,
        expert_pct,
        win_pct,
    )

    return SeriesProjection(
        sport=sport,
        higher_seed=higher_seed,
        lower_seed=lower_seed,
        conference=conference,
        projected_winner=winner,
        win_probability=win_pct,
        most_likely_result=ml_result,
        series_probs=dist,
        model_series_win_pct=model_higher_pct,
        expert_series_win_pct=expert_pct * 100 if expert_pct else 0.0,
        blurb=blurb,
    )
