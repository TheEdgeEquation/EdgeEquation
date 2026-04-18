# modes/smash/run.py

from core.posting import post_text
from core.formatting import format_smash_block
from engines.smash import post_smash


def run() -> None:
    """
    Smash of the Day Mode entrypoint.
    """
    payload = post_smash()
    text = format_smash_block(payload)

    post_text(
        text,
        mode="smash",
        payload=payload,
    )
