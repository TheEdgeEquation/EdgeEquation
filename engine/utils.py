import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


# ============================================================
# GAME START CHECK
# ============================================================

def game_has_started(play):
    """
    Returns True if the game's scheduled start time is in the past.
    Expects play["start_time"] to be an ISO timestamp or datetime.
    """
    try:
        start = play.get("start_time")
        if not start:
            return False

        if isinstance(start, str):
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        else:
            start_dt = start

        now = datetime.now(timezone.utc)
        return start_dt <= now

    except Exception as e:
        logger.error("game_has_started() failed: " + str(e))
        return False


# ============================================================
# DAILY CTA (CALL TO ACTION)
# ============================================================

def get_daily_cta():
    """
    Returns the standard EE 3.0 call-to-action footer.
    """
    return (
        "Follow for daily projections, edges, and model notes.\n"
        "Analytics. Not feelings."
    )
