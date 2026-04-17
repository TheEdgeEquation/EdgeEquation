# modes/spotlight/run.py

def _select_spotlight_insight():
    """
    Placeholder spotlight selector.
    Replace with your real model-driven logic later.
    """
    return {
        "text": (
            "When a pitcher increases slider usage above 38%, "
            "league-wide chase rate rises by 11%."
        ),
        "hashtags": "#MLB #Analytics"
    }


def run():
    """
    Spotlight Game Insight (3:30 PM CT)
    Placeholder-safe: prints instead of posting.
    """
    print("Running Spotlight Mode")

    insight = _select_spotlight_insight()

    print("Spotlight Game Insight:")
    print(insight["text"])
    print(insight["hashtags"])
