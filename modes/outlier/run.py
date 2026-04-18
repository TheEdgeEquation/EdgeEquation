# modes/outlier/run.py

from core.posting import post_text
from core.formatting import format_outlier_block
from engines.outlier import post_outlier


def run() -> None:
    """
    Outlier of the Day Mode entrypoint.
    """
    payload = post_outlier()
    text = format_outlier_block(payload)

    post_text(
        text,
        mode="outlier",
        payload=payload,
    )
