# modes/gotd/run.py
"""
Game of the Day (GOTD) Engine
The Edge Equation — Facts. Not Feelings.
"""

from core.posting import post_text
from core.formatting import format_gotd_block
from core.data_loader import load_games
from core.utils import now_timestamp


def _filter_gotd_candidates(games):
    """
    Filter to games with full model info.
    """
    out = []
    for g in games:
        if g.get("model_prob") is None or g.get("edge_ev") is None:
            continue
        out.append(g)
    return out


def _rank_gotd_candidates(games):
    """
    Rank by EV, then model probability.
    """
    return sorted(
        games,
        key=lambda x: (x.get("edge_ev", 0), x.get("model_prob", 0)),
        reverse=True,
    )


def _build_payload(g):
    return {
        "team": g.get("team"),  # side we’re backing
        "home_team": g.get("home_team"),
        "away_team": g.get("away_team"),
        "sport": g.get("sport"),
        "market": g.get("market"),
        "model_prob": g.get("model_prob"),
        "edge_ev": g.get("edge_ev"),
        "reason": g.get("reason"),
        "context": g.get("context"),
        "timestamp": now_timestamp(),
    }


def run():
    games = load_games()
    candidates = _filter_gotd_candidates(games)

    if not candidates:
        text = "🏆 Game of the Day\n\nNo qualified full-game edges today.\n\nFacts. Not Feelings."
        post_text(text, mode="gotd", payload={})
        return

    ranked = _rank_gotd_candidates(candidates)
    top = ranked[0]

    payload = _build_payload(top)
    text = format_gotd_block(payload)
    post_text(text, mode="gotd", payload=payload)
