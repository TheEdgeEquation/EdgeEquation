# modes/results/run.py

from datetime import datetime, timedelta

from core.posting import post_text
from core.formatting import format_results_block
from core.results_engine import build_results_payload


def _default_results_date() -> str:
    """
    By default, grade yesterday's slate in UTC.
    Returns YYYY-MM-DD.
    """
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def run(date_str: str | None = None) -> None:
    """
    Results Mode entrypoint.

    - Picks a date (default: yesterday)
    - Builds the results payload from WAL projections + results
    - Formats a premium results block
    - Posts via the unified posting engine
    """
    if date_str is None:
        date_str = _default_results_date()

    payload = build_results_payload(date_str)
    text = format_results_block(payload)

    post_text(
        text,
        mode="results",
        payload={
            "date": date_str,
            "engine_payload": payload,
        },
    )
