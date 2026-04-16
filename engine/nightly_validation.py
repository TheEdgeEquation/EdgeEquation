import logging
from datetime import date

logger = logging.getLogger(__name__)

# Global router for all sports
from engine.global_router import get_projections


# ─────────────────────────────────────────────
# VALIDATION RULES
# ─────────────────────────────────────────────

REQUIRED_FIELDS = [
    "sport",
    "league",
    "team_a",
    "team_b",
    "a_score",
    "b_score",
    "total",
    "game_date",
]

def validate_schema(game):
    missing = [f for f in REQUIRED_FIELDS if f not in game]
    return missing


def validate_numeric(game):
    issues = []

    if not isinstance(game.get("a_score"), (int, float)):
        issues.append("a_score not numeric")

    if not isinstance(game.get("b_score"), (int, float)):
        issues.append("b_score not numeric")

    if not isinstance(game.get("total"), (int, float)):
        issues.append("total not numeric")

    # Check total consistency
    try:
        expected = round(game["a_score"] + game["b_score"], 1)
        if abs(expected - game["total"]) > 0.1:
            issues.append(f"total mismatch (expected {expected}, got {game['total']})")
    except Exception:
        issues.append("total calculation failed")

    return issues


def validate_clv(game):
    issues = []
    clv = game.get("clv")

    if clv is None:
        issues.append("missing CLV")
        return issues

    if not isinstance(clv, (int, float)):
        issues.append("CLV not numeric")
        return issues

    if clv < -1 or clv > 1:
        issues.append(f"CLV out of bounds ({clv})")

    return issues


# ─────────────────────────────────────────────
# VALIDATION RUNNER
# ─────────────────────────────────────────────

def validate_league(sport: str, game_date: date):
    """
    Runs validation for a single league.
    Returns a dict of issues.
    """
    results = {
        "sport": sport,
        "games_found": 0,
        "schema_errors": [],
        "numeric_errors": [],
        "clv_errors": [],
    }

    games = get_projections(sport, game_date)
    results["games_found"] = len(games)

    for game in games:
        schema_issues = validate_schema(game)
        if schema_issues:
            results["schema_errors"].append({"game": game, "issues": schema_issues})

        numeric_issues = validate_numeric(game)
        if numeric_issues:
            results["numeric_errors"].append({"game": game, "issues": numeric_issues})

        clv_issues = validate_clv(game)
        if clv_issues:
            results["clv_errors"].append({"game": game, "issues": clv_issues})

    return results


# ─────────────────────────────────────────────
# NIGHTLY HARNESS
# ─────────────────────────────────────────────

ALL_SPORTS = [
    "mlb",
    "kbo",
    "npb",
    "nba",
    "nfl",
    "nhl",
    "epl",
    "ucl",
]

def run_nightly_validation(game_date: date = None):
    """
    Runs validation for all sports and prints a clean report.
    """
    if game_date is None:
        game_date = date.today()

    logger.info(f"Running nightly validation for {game_date}")

    report = {}

    for sport in ALL_SPORTS:
        try:
            results = validate_league(sport, game_date)
            report[sport] = results

            logger.info(
                f"[{sport.upper()}] games={results['games_found']} "
                f"schema={len(results['schema_errors'])} "
                f"numeric={len(results['numeric_errors'])} "
                f"clv={len(results['clv_errors'])}"
            )

        except Exception as e:
            logger.error(f"Validation failed for {sport}: {e}")
            report[sport] = {"error": str(e)}

    return report
