# modes/results/run.py

from datetime import datetime
from core.posting import post_text
from core.formatting import format_results_block

def build_results_payload():
    """
    Replace placeholder logic with your actual results engine.
    This is the premium 7-bullet structure for each pick.
    """

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",

        "results": [
            {
                "label": "Yankees ML",
                "outcome": "HIT",
                "key_metric": "31% K-rate advantage",
                "context": "Opp lineup 27% whiff rate",
                "model_signal": "+0.31 EV",
                "trend": "Bullpen +0.18 WPA",
                "matchup_delta": "+0.12 expected runs",
                "historical_comp": "Similar matchup +0.09 EV",
                "final_score": "5–2"
            },
            {
                "label": "Dodgers TT Over",
                "outcome": "MISS",
                "key_metric": "+0.18 xwOBA projection",
                "context": "Opp SP allows 43% hard contact",
                "model_signal": "+0.22 EV",
                "trend": "OPS +0.102 last 7 days",
                "matchup_delta": "+0.14 expected runs",
                "historical_comp": "Similar matchup +0.11 EV",
                "final_score": "3 runs"
            }
        ],

        "totals": {
            "correct": 1,
            "total": 2,
            "ev_delta": +0.09
        }
    }


def run():
    payload = build_results_payload()
    text = format_results_block(payload)
    post_text(text, mode="results", payload=payload)
