# core/utils.py
"""
Utility Layer for The Edge Equation.

This file provides:
- Timestamp helpers
- Safe numeric formatting
- ID generation
- Sanitization helpers

These utilities are intentionally minimal and stable.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Time Helpers
# ---------------------------------------------------------------------------

def now_timestamp() -> str:
    """
    Return an ISO-8601 UTC timestamp.
    Example: "2026-04-17T20:37:12Z"
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_date() -> str:
    """
    Return today's date in YYYY-MM-DD format (UTC).
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# ID Helpers
# ---------------------------------------------------------------------------

def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID with optional prefix.
    Example: "edge_3f92b1c2e8"
    """
    base = uuid.uuid4().hex[:10]
    return f"{prefix}{base}" if prefix else base


# ---------------------------------------------------------------------------
# Safe Numeric Formatting
# ---------------------------------------------------------------------------

def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """
    Convert to float if possible, else return default.
    """
    try:
        return float(value)
    except Exception:
        return default


def fmt_float(value: Any, decimals: int = 2, default: str = "N/A") -> str:
    """
    Format a float safely.
    """
    try:
        return f"{float(value):.{decimals}f}"
    except Exception:
        return default


# ---------------------------------------------------------------------------
# Safe Access Helpers
# ---------------------------------------------------------------------------

def safe_get(d: dict, key: str, default: Any = None) -> Any:
    """
    Safe dictionary access.
    """
    return d.get(key, default)


# ---------------------------------------------------------------------------
# Sanitization Helpers
# ---------------------------------------------------------------------------

def sanitize_probability(value: Any) -> Optional[float]:
    """
    Ensure probability is between 0 and 1.
    """
    try:
        v = float(value)
        if 0 <= v <= 1:
            return v
        return None
    except Exception:
        return None


def sanitize_ev(value: Any) -> Optional[float]:
    """
    Ensure EV is a valid float.
    """
    try:
        return float(value)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Logging Helpers
# ---------------------------------------------------------------------------

def log_timestamp() -> str:
    """
    Timestamp for logs (UTC).
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
