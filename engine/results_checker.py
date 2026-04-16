import logging

logger = logging.getLogger(__name__)


# ============================================================
# MLB GAME RESULTS
# ============================================================

def check_mlb_results(game_props):
    """
    Input: list of graded MLB game-level props
    Output: (hits, misses)
    """
    hits = []
    misses = []

    for p in game_props:
        try:
            if p.get("result_checked"):
                if p.get("hit"):
                    hits.append(p)
                else:
                    misses.append(p)
        except Exception as e:
            logger.error("MLB game result check failed: " + str(e))

    return hits, misses


# ============================================================
# MLB PITCHER RESULTS (K props)
# ============================================================

def check_pitcher_results(pitcher_props):
    """
    Input: list of graded MLB pitcher props (K)
    Output: (hits, misses)
    """
    hits = []
    misses = []

    for p in pitcher_props:
        try:
            if p.get("result_checked"):
                if p.get("hit"):
                    hits.append(p)
                else:
                    misses.append(p)
        except Exception as e:
            logger.error("Pitcher result check failed: " + str(e))

    return hits, misses


# ============================================================
# GLOBAL RESULTS (KBO, NPB, EPL, UCL)
# ============================================================

def check_global_results(global_props):
    """
    Input: list of graded global props
    Output: (hits, misses)
    """
    hits = []
    misses = []

    for p in global_props:
        try:
            if p.get("result_checked"):
                if p.get("hit"):
                    hits.append(p)
                else:
                    misses.append(p)
        except Exception as e:
            logger.error("Global result check failed: " + str(e))

    return hits, misses
