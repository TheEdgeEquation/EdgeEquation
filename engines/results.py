# engines/results.py
from core.twitter_client import post_text


def _fetch_hits() -> list[dict]:
    """
    Placeholder results fetcher.
    Later this will:
    - read your stored posted edges
    - check which ones hit
    - return a list of hits
    """
    return []  # safe default: no results posted


def post_results_if_any():
    hits = _fetch_hits()
    if not hits:
        return  # no post if nothing hit

    # Simple summary for now
    summary = (
        f"Posted edges that cleared today: {len(hits)}.\n"
        "Model performance continues to calibrate.\n"
        "#Analytics"
    )

    post_text(summary)
