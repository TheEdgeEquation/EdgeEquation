# modes/edges/evening.py

from datetime import datetime
from core.posting import post_text
from core.formatting import format_edges_block

def build_evening_edges():
    """
    Returns a dict with multi-team premium analytics.
    Replace placeholder logic with your model outputs.
    """

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "edges": [
            {
                "team": "Padres",
                "confidence": 0.60,
                "key_metric": "Bullpen ERA 2.41 over last 12 games",
                "context": "Opp lineup ranks 28th vs late-inning velocity",
                "trend": "Padres WHIP improved by 0.09 last 7 days",
                "matchup_delta": "-0.13 expected runs allowed",
                "historical_comp": "Similar matchup: -0.11 EV",
                "edge_summary": "Model favors SD in late-game suppression."
            },
            {
                "team": "Astros",
                "confidence": 0.57,
                "key_metric": "Lineup +0.21 xwOBA vs LHP",
                "context": "Opp SP allows 43% hard contact vs RHH",
                "trend": "Team OPS +0.134 last 10 games",
                "matchup_delta": "+0.17 expected runs",
                "historical_comp": "Comparable matchup: +0.15 EV",
                "edge_summary": "Model projects strong mid-game scoring window."
            }
        ]
    }


def run():
    payload = build_evening_edges()
    text = format_edges_block(payload)
    post_text(text, mode="edges_evening", payload=payload)
