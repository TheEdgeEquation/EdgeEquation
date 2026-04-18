# modes/potd/run.py

from core.posting import post_text
from core.formatting import format_potd_block
from engines.potd import post_potd


def run() -> None:
    """
    Prop of the Day Mode entrypoint.
    """
    payload = post_potd()
    text = format_potd_block(payload)

    post_text(
        text,
        mode="potd",
        payload=payload,
    )
