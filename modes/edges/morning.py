# modes/edges/morning.py

from datetime import datetime
from core.posting import post_text
from core.formatting import format_edges_block

def build_morning_edges():
    """
    Returns a dict with multi-team premium analytics.
    Replace placeholder logic with your model outputs.
    """

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "edges": [
            {
                "team": "Yankees",
                "confidence": 0.62,
                "key_metric": "Cole 31% K-rate vs lineup 27% whiff rate",
                "context": "Opp lineup struggles vs high-velocity 4-seamers",
                "trend": "Bullpen +0.18 WPA over last 14 days",
                "matchup_delta": "+0.12 expected runs vs SP",
                "historical_comp": "Similar matchup: +0.09 EV last season",
                "edge_summary": "Model favors NYY early scoring pressure."
            },
            {
                "team": "Dodgers",
                "confidence": 0.58,
                "key_metric": "Bullpen xFIP improved by 0.41 last 10 games",
                "context": "Opp lineup bottom 5 vs sliders",
                "trend": "Team OPS +0.102 over last week",
                "matchup_delta": "+0.14 xwOBA advantage",
                "historical_comp": "Comparable matchup yielded +0.11 EV",
                "edge_summary": "Model projects late-inning leverage edge."
            }
        ]
    }


def run():
    payload = build_morning_edges()
    text = format_edges_block(payload)
    post_text(text, mode="edges_morning", payload=payload)
