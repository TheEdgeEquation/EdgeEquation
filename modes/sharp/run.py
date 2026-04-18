# modes/sharp/run.py
"""
Sharp Signal Engine
The Edge Equation — Facts. Not Feelings.
"""

from core.posting import post_text
from core.formatting import format_sharp_block
from core.data_loader import load_games
from core.utils import now_timestamp


def _filter_sharp_candidates(games):
    """
    You can later add:
    - market movement alignment
    - consensus vs model checks
    For now: require model_prob + edge_ev + team + side.
    """
    out = []
    for g in games:
        if g.get("model_prob") is None or g.get("edge_ev") is None:
            continue
        if not g.get("team") or not g.get("side"):
            continue
        out.append(g)
    return out


def _rank_sharp_candidates(games):
    return sorted(
        games,
        key=lambda x: (x.get("edge_ev", 0), x.get("model_prob", 0)),
        reverse=True,
    )


def _build_payload(g):
    return {
        "team": g.get("team"),
        "side": g.get("side"),
        "sport": g.get("sport"),
        "market": g.get("market"),
        "model_prob": g.get("model_prob"),
        "edge_ev": g.get("edge_ev"),
        "reason": g.get("reason"),
        "timestamp": now_timestamp(),
    }


def run():
    games = load_games()
    candidates = _filter_sharp_candidates(games)

    if not candidates:
        text = "📊 Sharp Signal\n\nNo qualified sharp signals today.\n\nFacts. Not Feelings."
        post_text(text, mode="sharp", payload={})
        return

    ranked = _rank_sharp_candidates(candidates)
    top = ranked[0]

    payload = _build_payload(top)
    text = format_sharp_block(payload)
    post_text(text, mode="sharp", payload=payload)
