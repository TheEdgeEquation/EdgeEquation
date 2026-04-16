import logging

logger = logging.getLogger(__name__)

# Baseball (MLB, KBO, NPB)
from engine.baseball_router import get_baseball_projections

GLOBAL_SCRAPER_MAP = {
    "mlb": lambda date=None: get_baseball_projections("mlb", date),
    "kbo": lambda date=None: get_baseball_projections("kbo", date),
    "npb": lambda date=None: get_baseball_projections("npb", date),
}

def get_projections(sport: str, game_date=None):
    key = sport.lower().strip()

    if key not in GLOBAL_SCRAPER_MAP:
        logger.error(f"Unknown sport: {sport}")
        return []

    try:
        scraper = GLOBAL_SCRAPER_MAP[key]
        return scraper(game_date)
    except Exception as e:
        logger.error(f"Global scraper failed for {sport}: {e}")
        return []
