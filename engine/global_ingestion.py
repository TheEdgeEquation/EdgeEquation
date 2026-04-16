import logging
from datetime import date

from engine.global_router import get_projections
from engine.global_game_factory import build_game_list, Game

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# CORE INGESTION FUNCTIONS
# ─────────────────────────────────────────────

def ingest_sport(sport: str, game_date: date = None) -> list[Game]:
    """
    Ingests a single sport:
      1) Calls global router for raw projections
      2) Normalizes into canonical Game objects
    """
    if game_date is None:
        game_date = date.today()

    logger.info(f"Ingesting sport={sport} for date={game_date}")

    raw_games = get_projections(sport, game_date)
    if not raw_games:
        logger.info(f"No games returned for sport={sport} on {game_date}")
        return []

    games = build_game_list(raw_games)
    logger.info(f"Ingested {len(games)} games for sport={sport}")

    return games


def ingest_all_sports(sports: list[str] = None, game_date: date = None) -> list[Game]:
    """
    Ingests all configured sports and returns a flat list of Game objects.
    """
    if game_date is None:
        game_date = date.today()

    if sports is None:
        sports = [
            "mlb",
            "kbo",
            "npb",
            "nba",
            "nfl",
            "nhl",
            "epl",
            "ucl",
        ]

    logger.info(f"Global ingestion start for {game_date} (sports={sports})")

    all_games: list[Game] = []

    for sport in sports:
        try:
            games = ingest_sport(sport, game_date)
            all_games.extend(games)
        except Exception as e:
            logger.error(f"Ingestion failed for sport={sport}: {e}")

    # Optional: sort for deterministic downstream behavior
    all_games.sort(
        key=lambda g: (
            g.sport,
            g.league,
            g.game_date,
            (g.start_time or date.min),
            g.team_b,
            g.team_a,
        )
    )

    logger.info(
        f"Global ingestion complete for {game_date}: total_games={len(all_games)}"
    )

    return all_games


# ─────────────────────────────────────────────
# CONVENIENCE ENTRYPOINT
# ─────────────────────────────────────────────

def run_daily_ingestion(game_date: date = None) -> list[Game]:
    """
    High-level daily ingestion entrypoint.
    Intended to be called by schedulers / jobs.
    """
    return ingest_all_sports(game_date=game_date)
