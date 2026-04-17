from core.posting import post_text
from core.formatting import format_insight_block

def run():
    insight = build_kbo_npb_insight()
    text = format_insight_block("KBO/NPB Insight", insight)
    post_text(text, mode="fact_overseas", payload=insight)
