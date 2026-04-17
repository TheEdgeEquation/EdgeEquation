from core.posting import post_text
from core.formatting import format_insight_block

def run():
    insight = build_mlb_insight()  # your existing generator, just return a dict
    text = format_insight_block("MLB Insight", insight)
    post_text(text, mode="fact_domestic", payload=insight)
