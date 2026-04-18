# core/projections_logger.py
"""
Write-Ahead Logger (WAL) for The Edge Equation.

This logger records:
- posting events
- retries
- failures
- fallback triggers
- payload snapshots

Each event is written as a single JSONL line:
    data/wal/posts/YYYY-MM-DD.jsonl

This file NEVER raises exceptions.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from core.utils import generate_id, log_timestamp, today_date


# ---------------------------------------------------------------------------
# Directory Setup
# ---------------------------------------------------------------------------

BASE_DIR = Path("data") / "wal" / "posts"


def _ensure_dir() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# File Helpers
# ---------------------------------------------------------------------------

def _wal_file_for_today() -> Path:
    date_str = today_date()
    return BASE_DIR / f"{date_str}.jsonl"


# ---------------------------------------------------------------------------
# Core Logger
# ---------------------------------------------------------------------------

def log_post_event(
    mode: str,
    payload: Dict[str, Any],
    status: str,
    error: Optional[str] = None,
) -> None:
    """
    Append a single WAL event.

    Fields:
        event_id: unique ID
        timestamp: UTC timestamp
        mode: posting mode
        status: "success" | "retry" | "failed"
        payload: snapshot of what was attempted
        error: optional error message
    """

    try:
        _ensure_dir()
        wal_file = _wal_file_for_today()

        event = {
            "event_id": generate_id("post_"),
            "timestamp": log_timestamp(),
            "mode": mode,
            "status": status,
            "payload": payload,
        }

        if error:
            event["error"] = error

        with wal_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    except Exception:
        # Logging must NEVER break the system.
        pass
