# core/posting.py

import time
import random
from core.x_client import get_x_client

def _log(message: str):
    """Simple internal logger."""
    print(f"[POSTING] {message}")

def _retry(func, max_attempts=6, base_delay=2, max_delay=20):
    """
    Maximum-resilience retry logic with:
    - Exponential backoff
    - Jitter (randomized delay)
    - Targeted retry for transient X API failures
    - Hard cap to prevent runaway retries
    """
    for attempt in range(1, max_attempts + 1):
        try:
            return func()

        except Exception as e:
            error_text = str(e)

            # Only retry on transient X failures
            transient = (
                "503" in error_text or
                "Over capacity" in error_text or
                "Service Unavailable" in error_text or
                "Connection aborted" in error_text or
                "timed out" in error_text or
                "EOF occurred" in error_text or
                "RemoteDisconnected" in error_text
            )

            if not transient:
                raise

            # Exponential backoff with jitter
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            jitter = random.uniform(0.5, 1.5)
            sleep_time = delay * jitter

            _log(f"Transient error detected: {error_text}")
            _log(f"Retry {attempt}/{max_attempts} — sleeping {sleep_time:.2f}s")

            time.sleep(sleep_time)

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
        _retry(lambda: client.update_status(text))
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
        media = _retry(lambda: client.media_upload(image_path))
        _retry(lambda: client.update_status(status=text, media_ids=[media.media_id]))
        _log("Graphic post sent successfully")
    except Exception as e:
        _log(f"ERROR posting graphic: {e}")
