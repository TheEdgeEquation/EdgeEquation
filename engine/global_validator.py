import logging

logger = logging.getLogger("global_validator")

REQUIRED_FIELDS = [
    "sport",
    "team_a",
    "team_b",
    "total",
    "vegas_total",
    "closing_total",
]

def validate_global_game(game):
    """
    Validates a single global game object.
    Ensures all required fields exist and are not None.
    """

    errors = []

    for field in REQUIRED_FIELDS:
        if field not in game:
            errors.append(f"Missing field: {field}")
        elif game[field] is None:
            errors.append(f"Null field: {field}")

    # Ensure totals are numeric
    for field in ("total", "vegas_total", "closing_total"):
        try:
            float(game.get(field))
        except Exception:
            errors.append(f"Invalid numeric field: {field}")

    # Ensure matchup is present
    if not game.get("team_a") or not game.get("team_b"):
        errors.append("Missing team names")

    if errors:
        logger.error(f"Global validation failed for game {game}: {errors}")
        return False

    return True


def validate_global_list(games):
    """
    Validates a list of global games.
    Returns only valid games.
    Logs errors but never crashes the engine.
    """

    if not games:
        return games

    valid = []
    for g in games:
        if validate_global_game(g):
            valid.append(g)
        else:
            logger.error(f"Dropping invalid global game: {g}")

    return valid
