"""
Edge Equation — State Tracker
Maintains engine memory across runs.
Tracks what's been posted, recalibration status, slate status, alignment.
"""
 
import json
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
 
logger = logging.getLogger(__name__)
 
STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "state.json")
 
DEFAULT_STATE = {
    "last_GOTD_id": None,
    "last_POTD_id": None,
    "last_EE_projections_posted_at": None,
    "last_CBC_projections_posted_at": None,
    "last_EE_results_posted_at": None,
    "last_CBC_results_posted_at": None,
    "last_EE_cheeky_posted_at": None,
    "last_CBC_cheeky_posted_at": None,
    "last_EE_gotd_posted_at": None,
    "last_EE_potd_posted_at": None,
    "last_CBC_gotd_posted_at": None,
    "last_CBC_potd_posted_at": None,
    "last_system_status_posted_at": None,
    "last_midday_insight_posted_at": None,
    "last_evening_prop_posted_at": None,
    "last_cbc_nightshift_posted_at": None,
    "last_nrfi_posted_at": None,
 
    "recalibration_status": {
        "EE": True,
        "CBC": True
    },
 
    "slate_status": {
        "EE": "idle",
        "CBC": "idle"
    },
 
    "alignment_status": {
        "EE_GOTD": False,
        "EE_POTD": False,
        "CBC_GOTD": False,
        "CBC_POTD": False
    },
 
    "manual_override": {
        "EE_projections": False,
        "CBC_projections": False,
        "EE_results": False,
        "CBC_results": False,
        "EE_gotd": False,
        "EE_potd": False,
        "CBC_gotd": False,
        "CBC_potd": False,
    },
 
    "data_freshness": {
        "EE": True,
        "CBC": True
    },
 
    "today_date": None,
}
 
 
def _ensure_data_dir():
    data_dir = Path(STATE_FILE).parent
    data_dir.mkdir(parents=True, exist_ok=True)
 
 
def load_state() -> dict:
    """Load state from disk. Create default if not exists."""
    _ensure_data_dir()
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
            # Merge with defaults to catch any new keys
            merged = DEFAULT_STATE.copy()
            merged.update(state)
            return merged
    except Exception as e:
        logger.warning(f"State load failed: {e} — using defaults")
    return DEFAULT_STATE.copy()
 
 
def save_state(state: dict) -> bool:
    """Save state to disk."""
    _ensure_data_dir()
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"State save failed: {e}")
        return False
 
 
def reset_daily(state: dict) -> dict:
    """Reset daily flags when a new day starts."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("today_date") != today:
        logger.info(f"New day detected — resetting daily state ({today})")
        state["today_date"] = today
        state["alignment_status"] = {
            "EE_GOTD": False,
            "EE_POTD": False,
            "CBC_GOTD": False,
            "CBC_POTD": False,
        }
        state["manual_override"] = {k: False for k in state.get("manual_override", {})}
        state["recalibration_status"] = {"EE": True, "CBC": True}
        state["data_freshness"] = {"EE": True, "CBC": True}
    return state
 
 
def mark_posted(state: dict, post_type: str) -> dict:
    """Mark a post type as posted with current timestamp."""
    now = datetime.now(timezone.utc).isoformat()
    key = f"last_{post_type}_posted_at"
    if key in state:
        state[key] = now
        logger.info(f"[STATE] Marked posted: {post_type} at {now}")
    else:
        logger.warning(f"[STATE] Unknown post type: {post_type}")
    return state
 
 
def was_posted_today(state: dict, post_type: str) -> bool:
    """Check if a post type was already posted today."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    key = f"last_{post_type}_posted_at"
    last = state.get(key)
    if not last:
        return False
    return last.startswith(today)
 
 
def set_alignment(state: dict, brand: str, post_type: str, aligned: bool) -> dict:
    """Set alignment status for GOTD or POTD."""
    key = f"{brand}_{post_type}"
    if key in state.get("alignment_status", {}):
        state["alignment_status"][key] = aligned
        logger.info(f"[STATE] Alignment set: {key} = {aligned}")
    return state
 
 
def set_manual_override(state: dict, post_type: str, value: bool) -> dict:
    """Set manual override for a post type."""
    if post_type in state.get("manual_override", {}):
        state["manual_override"][post_type] = value
        logger.info(f"[STATE] Manual override: {post_type} = {value}")
    return state
 
 
def get_and_update() -> dict:
    """Load state, reset daily if needed, return."""
    state = load_state()
    state = reset_daily(state)
    save_state(state)
    return state
 
 
if __name__ == "__main__":
    state = get_and_update()
    print("Current state:")
    print(json.dumps(state, indent=2))
