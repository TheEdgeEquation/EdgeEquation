# modes/spotlight/run.py
"""
Spotlight Insight Engine
The Edge Equation — Facts. Not Feelings.
"""

from core.posting import post_text
from core.formatting import format_spotlight_block
from core.data_loader import load_props
from core.utils import now_timestamp


def _filter_spotlight_candidates(props):
    out = []
    for p in props:
        if not p.get("player"):
            continue
        if p.get("model_prob") is None or p.get("edge_ev") is None:
            continue
        out.append(p)
    return out


def _rank_spotlight_candidates(props):
    """
    You can tune this to be more matchup/storyline aware later.
    For now: EV then model probability.
    """
    return sorted(
        props,
        key=lambda x: (x.get("edge_ev", 0), x.get("model_prob", 0)),
        reverse=True,
    )


def _build_payload(p):
    return {
        "player": p.get("player"),
        "line": p.get("line"),
        "side": p.get("side"),
        "sport": p.get("sport"),
        "market": p.get("market"),
        "model_prob": p.get("model_prob"),
        "edge_ev": p.get("edge_ev"),
        "reason": p.get("reason"),
        "timestamp": now_timestamp(),
    }


def run():
    props = load_props()
    candidates = _filter_spotlight_candidates(props)

    if not candidates:
        text = "🔦 Spotlight Insight\n\nNo qualified spotlight edges today.\n\nFacts. Not Feelings."
        post_text(text, mode="spotlight", payload={})
        return

    ranked = _rank_spotlight_candidates(candidates)
    top = ranked[0]

    payload = _build_payload(top)
    text = format_spotlight_block(payload)
    post_text(text, mode="spotlight", payload=payload)
