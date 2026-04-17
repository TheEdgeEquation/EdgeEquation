# modes/facts/overseas.py

from datetime import datetime
from core.posting import post_text
from core.formatting import format_insight_block

def build_kbo_npb_insight():
    """
    Returns a dict with the 7-bullet KBO/NPB insight structure.
    Replace placeholder logic with your model outputs.
    """

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "key_metric": "Pitcher ground-ball rate 58% over last 5 starts",
        "context": "Opponent lineup ranks bottom 3 in hard-contact vs sinkers",
        "model_signal": "-0.31 expected runs vs market projection",
        "trend": "Team ERA improved by 0.42 over last 10 games",
        "matchup_delta": "-0.17 xwOBA allowed vs today's lineup profile",
        "historical_comp": "Similar matchup trend produced -0.28 EV last season",
        "edge_summary": "Model favors a suppressed scoring environment."
    }


def run():
    insight = build_kbo_npb_insight()
    text = format_insight_block("KBO/NPB Insight", insight)
    post_text(text, mode="fact_overseas", payload=insight)
