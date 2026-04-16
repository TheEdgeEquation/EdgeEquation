import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# CANONICAL GAME OBJECT
# ─────────────────────────────────────────────

class Game:
    """
    Canonical, engine‑safe game object used across ALL sports.
    Every scraper feeds into this. Every renderer and model consumes this.
    """

    def __init__(
        self,
        sport: str,
        league: str,
        team_a: str,
        team_b: str,
        a_score: float,
        b_score: float,
        total: float,
        game_date: date,
        clv: float = None,
        start_time: datetime = None,
        metadata: dict = None,
    ):
        self.sport = sport.lower().strip()
        self.league = league.upper().strip()

        self.team_a = team_a
        self.team_b = team_b

        self.a_score = float(a_score)
        self.b_score = float(b_score)
        self.total = float(total)

        self.game_date = game_date
        self.clv = clv
        self.start_time = start_time

        self.metadata = metadata or {}

    def to_dict(self):
        """
        Convert to a clean dict for posting, rendering, or storage.
        """
        return {
            "sport": self.sport,
            "league": self.league,
            "team_a": self.team_a,
            "team_b": self.team_b,
            "a_score": self.a_score,
            "b_score": self.b_score,
            "total": self.total,
            "game_date": self.game_date,
            "clv": self.clv,
            "start_time": self.start_time,
            "metadata": self.metadata,
        }

    def __repr__(self):
        return (
            f"Game({self.sport.upper()} {self.team_a} @ {self.team_b}, "
            f"{self.a_score}-{self.b_score}, total={self.total}, clv={self.clv})"
        )


# ─────────────────────────────────────────────
# FACTORY FUNCTION
# ─────────────────────────────────────────────

def build_game_object(raw: dict):
    """
    Converts a raw scraper dict into a canonical Game object.
    Ensures schema consistency across ALL sports.
    """

    required = [
        "sport",
        "league",
        "team_a",
        "team_b",
        "a_score",
        "b_score",
        "total",
        "game_date",
    ]

    missing = [f for f in required if f not in raw]
    if missing:
        logger.error(f"Game factory: missing fields {missing} in raw object: {raw}")
        return None

    return Game(
        sport=raw["sport"],
        league=raw["league"],
        team_a=raw["team_a"],
        team_b=raw["team_b"],
        a_score=raw["a_score"],
        b_score=raw["b_score"],
        total=raw["total"],
        game_date=raw["game_date"],
        clv=raw.get("clv"),
        start_time=raw.get("start_time"),
        metadata=raw.get("metadata", {}),
    )


# ─────────────────────────────────────────────
# BATCH CONVERSION
# ─────────────────────────────────────────────

def build_game_list(raw_list: list):
    """
    Converts a list of raw game dicts into a list of canonical Game objects.
    Filters out invalid entries automatically.
    """
    games = []

    for raw in raw_list:
        game = build_game_object(raw)
        if game:
            games.append(game)

    return games
