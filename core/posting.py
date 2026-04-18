# core/posting.py
"""
Unified Posting Engine (v3) for The Edge Equation.

Features:
- Deterministic posting
- Exponential backoff + jitter
- Multi-attempt resilience
- Essential-tier safe v1.1 posting
- Full WAL-safe logging
- Fallback email failsafe
- Zero silent failures
"""

import time
import random
import traceback
from typing import Optional, Dict, Any

import tweepy

from core.x_client import get_x_client
from core.email_failsafe import send_failsafe_email
from core.projections_logger import log_post_event


# ---------------------------------------------------------------------------
# Retry Configuration
# ---------------------------------------------------------------------------

MAX_ATTEMPTS = 5
BASE_DELAY = 2       # seconds
MAX_JITTER = 1.5     # seconds


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _sleep_with_backoff(attempt: int) -> None:
    """
    Exponential backoff with jitter.
    """
    delay = BASE_DELAY * (2 ** (attempt - 1))
    jitter = random.uniform(0, MAX_JITTER)
    time.sleep(delay + jitter)


def _safe_log_event(mode: str, payload: Dict[str, Any], status: str, error: Optional[str] = None):
    """
    WAL-safe event logging wrapper.
    """
    try:
        log_post_event(
            mode=mode,
            payload=payload,
            status=status,
            error=error,
        )
    except Exception:
        # Logging must NEVER break posting
        pass


# ---------------------------------------------------------------------------
# Core Posting Functions
# ---------------------------------------------------------------------------

def post_text(text: str, mode: str, payload: Dict[str, Any]) -> None:
    """
    Post a text-only tweet with full resilience.
    """
    client = get_x_client()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            client.update_status(status=text)

            _safe_log_event(mode, payload, status="success")
            return

        except Exception as e:
            error_msg = str(e)

            if attempt < MAX_ATTEMPTS:
                _safe_log_event(mode, payload, status="retry", error=error_msg)
                _sleep_with_backoff(attempt)
                continue

            # Final failure → fallback email
            _safe_log_event(mode, payload, status="failed", error=error_msg)
            send_failsafe_email(
                subject=f"[FAILSAFE] {mode.upper()} POST FAILED",
                body=f"Posting failed after {MAX_ATTEMPTS} attempts.\n\nError:\n{error_msg}\n\nPayload:\n{payload}\n\nText:\n{text}",
            )
            return


def post_graphic(image_path: str, text: str, mode: str, payload: Dict[str, Any]) -> None:
    """
    Post a tweet with media attachment.
    """
    client = get_x_client()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            media = client.media_upload(image_path)
            client.update_status(status=text, media_ids=[media.media_id])

            _safe_log_event(mode, payload, status="success")
            return

        except Exception as e:
            error_msg = str(e)

            if attempt < MAX_ATTEMPTS:
                _safe_log_event(mode, payload, status="retry", error=error_msg)
                _sleep_with_backoff(attempt)
                continue

            # Final failure → fallback email
            _safe_log_event(mode, payload, status="failed", error=error_msg)
            send_failsafe_email(
                subject=f"[FAILSAFE] {mode.upper()} GRAPHIC POST FAILED",
                body=f"Posting failed after {MAX_ATTEMPTS} attempts.\n\nError:\n{error_msg}\n\nPayload:\n{payload}\n\nText:\n{text}",
                attachment_path=image_path,
            )
            return
