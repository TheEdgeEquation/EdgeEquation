# modes/spotlight/run.py

from datetime import datetime
from core.posting import post_text
from core.formatting import format_spotlight_block

def build_spotlight_insight():
    """
    Returns a dict with the 7-bullet Spotlight structure.
    Replace placeholder logic with your model outputs.
    """

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sport": "NBA",
        "player": "Luka Doncic",
        "prop": "Over 8.5 assists",
        "confidence": 0.63,
        "key_metric": "17.4 potential assists per game vs this defense",
        "context": "Opp defense bottom 5 in perimeter rotations",
        "model_signal": "+0.7 assists above market projection",
        "trend": "Usage rate 34.7% over last 10 games",
        "matchup_delta": "+4.8 projected possessions above league average",
        "historical_comp": "Similar matchup: +1.1 assists above expectation",
        "edge_summary": "Model favors elevated assist volume in this pace environment."
    }


def run():
    payload = build_spotlight_insight()
    text = format_spotlight_block(payload)
    post_text(text, mode="spotlight", payload=payload)
