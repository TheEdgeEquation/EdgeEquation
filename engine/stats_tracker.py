import logging

logger = logging.getLogger(__name__)


# ============================================================
# WRAPPERS FOR EXISTING STATS MODULES
# ============================================================

try:
    from engine.weekly_summary import build_weekly_stats as _weekly
except Exception:
    _weekly = None

try:
    from engine.stats_summary import build_all_time_stats as _all_time
except Exception:
    _all_time = None


# ============================================================
# PUBLIC API — EXACTLY WHAT main.py EXPECTS
# ============================================================

def build_weekly_stats(style="ee"):
    """
    Returns weekly graded-output statistics.
    """
    if _weekly:
        try:
            return _weekly(style=style)
        except Exception as e:
            logger.error("Weekly stats failed: " + str(e))
            return {"total": 0}

    logger.error("Underlying weekly stats engine missing")
    return {"total": 0}


def build_all_time_stats(style="ee"):
    """
    Returns all-time graded-output statistics.
    """
    if _all_time:
        try:
            return _all_time(style=style)
        except Exception as e:
            logger.error("All-time stats failed: " + str(e))
            return {"total": 0}

    logger.error("Underlying all-time stats engine missing")
    return {"total": 0}
