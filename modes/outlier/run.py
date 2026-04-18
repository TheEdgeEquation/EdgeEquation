# modes/outlier/run.py
"""
Outlier of the Day Engine
The Edge Equation — Facts. Not Feelings.
"""

from core.posting import post_text
from core.formatting import format_outlier_block
from core.data_loader import load_props
from core.utils import now_timestamp


def _filter_outlier_candidates(props):
    out = []
    for p in props:
        if not p.get("player"):
            continue
        if p.get("model_prob") is None or p.get("edge_ev") is None:
            continue
        out.append(p)
    return out


def _rank_outlier_candidates(props):
    """
    Outlier = biggest model vs market gap.
    For now we treat EV as that proxy.
    """
    return sorted(
        props,
        key=lambda x: x.get("edge_ev", 0),
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
    candidates = _filter_outlier_candidates(props)

    if not candidates:
        text = "📈 Outlier of the Day\n\nNo qualified outlier edges today.\n\nFacts. Not Feelings."
        post_text(text, mode="outlier", payload={})
        return

    ranked = _rank_outlier_candidates(candidates)
    top = ranked[0]

    payload = _build_payload(top)
    text = format_outlier_block(payload)
    post_text(text, mode="outlier", payload=payload)
