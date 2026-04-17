# core/posting.py

import time
from core.emailer import send_fallback_email

# These helpers already exist in your system
from core.wal import write_wal, clear_wal
from core.dlq import write_dlq
from core.x_client import attempt_post  # your existing X posting function


def post_text(text: str, mode: str = "unknown"):
    """
    Durable text posting with:
    - WAL
    - retries
    - DLQ
    - fallback email
    """

    # 1. WAL write
    wal_id = write_wal(text, mode)

    # 2. Retry loop (your existing retry logic)
    max_retries = 3
    delay = 3

    for attempt in range(1, max_retries + 1):
        try:
            attempt_post(text)  # your existing X API call
            clear_wal(wal_id)
            return True

        except Exception as e:
            error_msg = str(e)

            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2  # exponential backoff
            else:
                # Final failure
                break

    # 3. DLQ write
    write_dlq(text, mode, error_msg)

    # 4. Fallback email
    send_fallback_email(
        mode=mode,
        text=text,
        error=error_msg,
        wal_id=wal_id
    )

    return False
