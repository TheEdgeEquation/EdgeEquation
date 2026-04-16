import logging

logger = logging.getLogger(__name__)

# Baseball
from engine.baseball_router import get_baseball_projections


# Football (NFL)
from engine.nfl_scraper import get_nfl_projections

# Hockey (NHL)
from engine.nhl_scraper import get_nhl_projections

# Soccer
from engine.soccer_scrapers import (
    get_epl_projections,
    get_ucl_projections,
)

# Map sport → projection function
GLOBAL_SCRAPER_MAP = {
    # Baseball
    "mlb": lambda date=None: get_baseball_projections("mlb", date),
    "kbo": lambda date=None: get_baseball_projections("kbo", date),
    "npb": lambda date=None: get_baseball_projections("npb", date),


    # Football
    "nfl": get_nfl_projections,

    # Hockey
    "nhl": get_nhl_projections,

    # Soccer
    "epl": get_epl_projections,
    "ucl": get_ucl_projections,
}


def get_projections(sport: str, game_date=None):
    """
    Global unified entrypoint for ALL sports.
    Example:
        get_projections("mlb")
        get_projections("nba")
        get_projections("epl")
    """
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
