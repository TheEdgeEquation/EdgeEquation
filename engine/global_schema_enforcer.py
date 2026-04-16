import logging
from datetime import date, datetime

logger = logging.getLogger("global_schema_enforcer")

# The official 3.0 schema
REQUIRED_FIELDS = {
    "sport": str,
    "league": str,
    "team_a": str,
    "team_b": str,
    "matchup": str,
    "a_score": (int, float),
    "b_score": (int, float),
    "total": (int, float),
    "model_total": (int, float),
    "vegas_total": (int, float),
    "closing_total": (int, float),
    "game_date": date,
}

OPTIONAL_FIELDS = {
    "start_time": (datetime, type(None)),
    "status": (str, type(None)),
    "edge": (float, type(None)),
    "source": (str, type(None)),
}

def enforce_schema(game):
    """
    Ensures a global game object conforms to the official 3.0 schema.
    Auto-fixes missing fields using safe defaults.
    """

    fixed = dict(game)  # shallow copy

    # -----------------------------
    # REQUIRED FIELDS
    # -----------------------------
    for field, expected_type in REQUIRED_FIELDS.items():

        # Missing field → auto-fill
        if field not in fixed:
            logger.warning(f"[SchemaEnforcer] Missing field '{field}', auto-filling.")
            fixed[field] = _default_value(field, fixed)

        # Null field → auto-fill
        elif fixed[field] is None:
            logger.warning(f"[SchemaEnforcer] Null field '{field}', auto-filling.")
            fixed[field] = _default_value(field, fixed)

        # Wrong type → attempt to coerce
        elif not isinstance(fixed[field], expected_type):
            try:
                fixed[field] = _coerce_value(field, fixed[field])
            except Exception:
                logger.error(f"[SchemaEnforcer] Invalid type for '{field}', auto-filling.")
                fixed[field] = _default_value(field, fixed)

    # -----------------------------
    # OPTIONAL FIELDS
    # -----------------------------
    for field, expected_type in OPTIONAL_FIELDS.items():
        if field not in fixed:
            fixed[field] = None

    return fixed


def enforce_schema_list(games):
    """
    Applies schema enforcement to a list of global games.
    """
    return [enforce_schema(g) for g in games]


# ---------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------

def _default_value(field, game):
    """
    Provides safe defaults for missing fields.
    """

    if field in ("total", "model_total"):
        a = game.get("a_score") or 0
        b = game.get("b_score") or 0
        return round(a + b, 1)

    if field in ("vegas_total", "closing_total"):
        # fallback to model total
        a = game.get("a_score") or 0
        b = game.get("b_score") or 0
        return round(a + b, 1)

    if field == "matchup":
        return f"{game.get('team_a', '?')} @ {game.get('team_b', '?')}"

    if field == "sport":
        return "unknown"

    if field == "league":
        return "UNKNOWN"

    if field == "team_a":
        return "Unknown A"

    if field == "team_b":
        return "Unknown B"

    if field == "game_date":
        return date.today()

    return None


def _coerce_value(field, value):
    """
    Attempts to coerce incorrect types into correct ones.
    """

    if field in ("a_score", "b_score", "total", "model_total", "vegas_total", "closing_total"):
        return float(value)

    if field == "matchup":
        return str(value)

    if field in ("sport", "league", "team_a", "team_b", "status", "source"):
        return str(value)

    return value
