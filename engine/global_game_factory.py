import logging
from datetime import date, datetime

logger = logging.getLogger("global_game_factory")

def build_global_game(
    sport: str,
    league: str,
    team_a: str,
    team_b: str,
    a_score: float,
    b_score: float,
    game_date: date,
    start_time: datetime = None,
    status: str = None,
    vegas_total: float = None,
    closing_total: float = None,
    source: str = "scraper"
):
    """
    EDGE EQUATION 3.0 — Unified Global Game Factory
    Produces a fully schema-compliant global game object.
    """

    # Model total
    model_total = round((a_score or 0) + (b_score or 0), 1)

    # Market totals (may be placeholders)
    vegas = vegas_total if vegas_total is not None else model_total
    closing = closing_total if closing_total is not None else vegas

    game = {
        # Core identifiers
        "sport": sport,
        "league": league,

        # Matchup
        "team_a": team_a,
        "team_b": team_b,
        "matchup": f"{team_a} @ {team_b}",

        # Model outputs
        "a_score": a_score,
        "b_score": b_score,
        "total": model_total,
        "model_total": model_total,

        # Market data (CLV)
        "vegas_total": vegas,
        "closing_total": closing,

        # Metadata
        "game_date": game_date,
        "start_time": start_time,
        "status": status,

        # Internal
        "edge": None,
        "source": source,
    }

    return game
