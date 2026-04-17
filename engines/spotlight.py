# engines/spotlight.py
from core.twitter_client import post_text


def _select_spotlight_game() -> dict:
    """
    Placeholder spotlight selector.
    Later this will pull from your model:
    - biggest game of the night
    - highest leverage matchup
    - most interesting pitching or lineup signal
    """
    return {
        "text": "When a pitcher’s slider usage jumps above 38%, league-wide chase rate increases by 11%.",
        "hashtags": "#MLB #Analytics"
    }


def post_spotlight_insight():
    game = _select_spotlight_game()

    status = (
        "Spotlight Game Insight:\n"
        f"{game['text']}\n\n"
        "The engine notices patterns.\n"
        f"{game['hashtags']}"
    )

    post_text(status)
