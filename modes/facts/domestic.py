# modes/facts/domestic.py

from datetime import datetime
from core.posting import post_text
from core.formatting import format_insight_block

def build_mlb_insight():
    """
    Returns a dict with the 7-bullet MLB insight structure.
    Replace the placeholder logic with your model outputs.
    """

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "key_metric": "Hard-hit rate spike of +7.4% over last 10 games",
        "context": "Opposing starter allows 42% hard contact vs RHH",
        "model_signal": "+0.22 expected runs above market projection",
        "trend": "Team OPS +0.118 over last 7 days",
        "matchup_delta": "+0.15 xwOBA advantage vs today's pitcher",
        "historical_comp": "Similar matchup profile produced +0.19 EV last season",
        "edge_summary": "Model projects meaningful run-production upside today."
    }


def run():
    insight = build_mlb_insight()
    text = format_insight_block("MLB Insight", insight)
    post_text(text, mode="fact_domestic", payload=insight)
