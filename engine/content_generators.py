import logging

logger = logging.getLogger(__name__)


# ============================================================
# WRAPPERS FOR EXISTING CONTENT GENERATORS
# ============================================================

# These imports match your existing engine structure.
# If any module name differs, tell me and I’ll adjust instantly.

try:
    from engine.gotd_potd_generator import (
        generate_gotd_from_play as _gotd,
        generate_potd_from_play as _potd,
    )
except Exception:
    _gotd = None
    _potd = None

try:
    from engine.first_inning_generator import (
        generate_first_inning_from_play as _fi,
    )
except Exception:
    _fi = None

try:
    from engine.results_generator import (
        generate_results_post as _results_post,
        generate_called_it_post as _called_it,
        generate_daily_accuracy_post as _accuracy,
    )
except Exception:
    _results_post = None
    _called_it = None
    _accuracy = None

try:
    from engine.weekly_generator import caption_weekly as _caption_weekly
except Exception:
    _caption_weekly = None


# ============================================================
# PUBLIC API — EXACTLY WHAT main.py EXPECTS
# ============================================================

def generate_gotd_from_play(play):
    if _gotd:
        return _gotd(play)
    logger.error("generate_gotd_from_play() missing underlying implementation")
    return ""


def generate_potd_from_play(play):
    if _potd:
        return _potd(play)
    logger.error("generate_potd_from_play() missing underlying implementation")
    return ""


def generate_first_inning_from_play(play):
    if _fi:
        return _fi(play)
    logger.error("generate_first_inning_from_play() missing underlying implementation")
    return ""


def generate_results_post(results):
    if _results_post:
        return _results_post(results)
    logger.error("generate_results_post() missing underlying implementation")
    return ""


def generate_called_it_post(hits, label):
    if _called_it:
        return _called_it(hits, label)
    logger.error("generate_called_it_post() missing underlying implementation")
    return ""


def generate_daily_accuracy_post(game_hits, game_misses, pitcher_hits, pitcher_misses):
    if _accuracy:
        return _accuracy(game_hits, game_misses, pitcher_hits, pitcher_misses)
    logger.error("generate_daily_accuracy_post() missing underlying implementation")
    return ""


def caption_weekly(stats):
    if _caption_weekly:
        return _caption_weekly(stats)
    logger.error("caption_weekly() missing underlying implementation")
    return "Weekly Summary Unavailable"
