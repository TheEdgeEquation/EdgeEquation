# modes/spotlight/run.py

from datetime import datetime
from core.posting import post_text
from core.formatting import format_spotlight_block
from engines.spotlight import post_spotlight


def run() -> None:
    """
    Spotlight Mode entrypoint.

    - Generates spotlight pick via spotlight engine
    - Logs projection to WAL (inside post_spotlight)
    - Formats premium spotlight block
    - Posts via unified posting engine
    """

    # 1. Generate spotlight pick + log projection
    payload = post_spotlight()

    # 2. Format spotlight text block
    text = format_spotlight_block(payload)

    # 3. Post to X using unified posting engine
    post_text(
        text,
        mode="spotlight",
        payload=payload,
    )
