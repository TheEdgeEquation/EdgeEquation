# core/posting.py

import time
from core.x_client import get_x_client

def _log(message: str):
    """Simple internal logger."""
    print(f"[POSTING] {message}")

import time

def _retry(func, max_attempts=3, delay=3):
    """
    Retry wrapper for transient X API errors (503, over capacity).
    """
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except Exception as e:
            if "503" in str(e) or "Over capacity" in str(e):
                print(f"[POSTING] Retry {attempt}/{max_attempts} after 503 Over Capacity")
                time.sleep(delay)
            else:
                raise
    raise Exception("Max retries reached for posting")


def post_text(text: str):
    """
    Unified text posting function.
    All automated modes call this.
    """
    _log("Preparing text post")

    if not text or not text.strip():
        _log("ERROR: Empty text passed to post_text()")
        return

    client = get_x_client()

    try:
        client.update_status(text)
        _log("Text post sent successfully")
    except Exception as e:
        _log(f"ERROR posting text: {e}")

def post_graphic(text: str, image_path: str):
    """
    Unified graphic posting function.
    Manual graphic modes call this.
    """
    _log("Preparing graphic post")

    if not text or not text.strip():
        _log("ERROR: Empty text passed to post_graphic()")
        return

    client = get_x_client()

    try:
        media = client.media_upload(image_path)
        client.update_status(status=text, media_ids=[media.media_id])
        _log("Graphic post sent successfully")
    except Exception as e:
        _log(f"ERROR posting graphic: {e}")
