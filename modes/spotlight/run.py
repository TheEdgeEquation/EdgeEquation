from core.posting import post_text

def _select_spotlight_insight():
    return (
        "When a pitcher increases slider usage above 38%, "
        "league-wide chase rate rises by 11%."
    )

def run():
    print("Running Spotlight Mode")

    insight = _select_spotlight_insight()

    text = (
        "🔦 Spotlight Insight\n\n"
        f"{insight}\n\n"
        "#MLB #AnalyticsNotFeelings"
    )

    post_text(text)
