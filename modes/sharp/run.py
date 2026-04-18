# modes/sharp/run.py

from core.posting import post_text
from core.formatting import format_sharp_block
from engines.sharp import post_sharp


def run() -> None:
    """
    Sharp Signal Mode entrypoint.
    """
    payload = post_sharp()
    text = format_sharp_block(payload)

    post_text(
        text,
        mode="sharp",
        payload=payload,
    )
