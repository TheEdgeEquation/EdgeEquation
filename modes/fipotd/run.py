# modes/fipotd/run.py
"""
First Inning Prop of the Day (FIPOTD) Engine
The Edge Equation — Facts. Not Feelings.

This mode selects the top NRFI/YRFI play based on:
- model probability
- EV
- matchup context
- MLB-only filtering
"""

from core.posting import post_text
from core.formatting import format_fipotd_block
from core.data_loader import load_props  # your existing loader
from core.utils import now_timestamp


def _filter_first_inning_props(props):
    """
    Keep only MLB NRFI/YRFI props.
    """
    valid_markets = {"NRFI", "YRFI"}
    out = []

    for p in props:
        sport = p.get("sport")
        market = p.get("market", "").upper()

        if sport == "MLB" and market in valid_markets:
            out.append(p)

    return out


def _rank_fipotd_candidates(props):
    """
    Rank by:
    1. Highest EV
    2. Highest model probability
    """
    return sorted(
        props,
        key=lambda x: (
            x.get("edge_ev", 0),
            x.get("model_prob", 0),
        ),
        reverse=True,
    )


def _build_payload(p):
    """
    Build the payload for the formatter.
    """
    return {
        "matchup": f"{p.get('away_team')} @ {p.get('home_team')}",
        "market": p.get("market"),
        "side": p.get("side"),
        "model_prob": p.get("model_prob"),
        "edge_ev": p.get("edge_ev"),
        "reason": p.get("reason"),
        "timestamp": now_timestamp(),
    }


def run():
    """
    Main FIPOTD runner.
    """
    # Load all props
    props = load_props()

    # Filter to MLB NRFI/YRFI only
    candidates = _filter_first_inning_props(props)

    if not candidates:
        text = "⏱️ First Inning Prop of the Day\n\nNo qualified NRFI/YRFI edges today.\n\nFacts. Not Feelings."
        post_text(text, mode="fipotd", payload={})
        return

    # Rank candidates
    ranked = _rank_fipotd_candidates(candidates)
    top = ranked[0]

    # Build payload
    payload = _build_payload(top)

    # Format text
    text = format_fipotd_block(payload)

    # Post
    post_text(text, mode="fipotd", payload=payload)
