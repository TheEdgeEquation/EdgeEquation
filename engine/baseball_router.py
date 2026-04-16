import logging

logger = logging.getLogger(__name__)

# Import league-specific scrapers
from engine.mlb_scraper import get_mlb_projections
from engine.international_scrapers import (
    get_kbo_projections,
    get_npb_projections,
)

# Map league → projection function
BASEBALL_SCRAPER_MAP = {
    "mlb": get_mlb_projections,
    "kbo": get_kbo_projections,
    "npb": get_npb_projections,
}


def get_baseball_projections(league: str, game_date=None):
    """
    Unified entrypoint for all baseball scrapers.
    Example:
        get_baseball_projections("mlb")
        get_baseball_projections("kbo")
        get_baseball_projections("npb")
    """
    key = league.lower().strip()

    if key not in BASEBALL_SCRAPER_MAP:
        logger.error(f"Unknown baseball league: {league}")
        return []

    try:
        scraper = BASEBALL_SCRAPER_MAP[key]
        return scraper(game_date)

    except Exception as e:
        logger.error(f"Baseball scraper failed for {league}: {e}")
        return []
