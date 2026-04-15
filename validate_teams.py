"""
Global Team Name Validator — Strict Mode Compatible
---------------------------------------------------

This module now provides:

    run_global_validation() → (ok: bool, issues: list[str])

Strict Mode uses this to decide whether posting is allowed.
"""

from pprint import pprint

# Odds API adapters
from engine.odds_api_client import (
    fetch_nba_standings,
    fetch_nhl_standings,
    fetch_nfl_standings,
    fetch_mlb_standings,
)

# Convert to TeamRecord
from engine.standings_to_records import convert_to_team_records

# Bracket builders
from engine.nba_bracket import build_nba_bracket
from engine.nhl_bracket import build_nhl_bracket

# Playoff engine (TEAM_STRENGTH lives here)
from engine.playoff_engine import TEAM_STRENGTH

# Team normalizer
from engine.team_normalizer import normalize_team_name


def extract_team_names_from_odds_api(fetch_func, sport):
    try:
        raw = fetch_func()
        records = convert_to_team_records(raw, sport=sport)
        return {normalize_team_name(r.team) for r in records}
    except Exception as e:
        return set(), f"[ERROR] Failed fetching {sport.upper()} standings: {e}"


def extract_team_names_from_strength_dict():
    return {normalize_team_name(t) for t in TEAM_STRENGTH.keys()}


def validate_league(league_name, fetch_func, bracket_builder=None):
    issues = []

    # 1. Odds API names
    odds_names = extract_team_names_from_odds_api(fetch_func, league_name)
    if isinstance(odds_names, tuple):
        odds_names, err = odds_names
        issues.append(err)

    # 2. Model dictionary names
    model_names = extract_team_names_from_strength_dict()

    # 3. Bracket names (if applicable)
    bracket_names = set()
    if bracket_builder:
        try:
            raw = fetch_func()
            records = convert_to_team_records(raw, sport=league_name)
            matchups = bracket_builder(records)
            for m in matchups:
                bracket_names.add(normalize_team_name(m["higher_seed"]))
                bracket_names.add(normalize_team_name(m["lower_seed"]))
        except Exception as e:
            issues.append(f"[ERROR] Bracket builder failed for {league_name}: {e}")

    # -------------------------
    # VALIDATION
    # -------------------------

    missing_in_model = odds_names - model_names
    missing_in_odds = model_names - odds_names

    if missing_in_model:
        issues.append(
            f"[WARNING] Teams in Odds API but NOT in model strength dict: {missing_in_model}"
        )

    if missing_in_odds:
        issues.append(
            f"[WARNING] Teams in model strength dict but NOT in Odds API: {missing_in_odds}"
        )

    if bracket_names:
        missing_in_model_from_bracket = bracket_names - model_names
        if missing_in_model_from_bracket:
            issues.append(
                f"[WARNING] Teams in bracket but NOT in model strength dict: {missing_in_model_from_bracket}"
            )

        missing_in_odds_from_bracket = bracket_names - odds_names
        if missing_in_odds_from_bracket:
            issues.append(
                f"[WARNING] Teams in bracket but NOT in Odds API standings: {missing_in_odds_from_bracket}"
            )

    ok = len(issues) == 0
    return ok, issues


def run_global_validation():
    """
    Runs validation for all leagues and returns:
        ok: bool
        issues: list[str]
    """
    all_issues = []

    # NBA
    ok, issues = validate_league("nba", fetch_nba_standings, build_nba_bracket)
    all_issues.extend(issues)

    # NHL
    ok2, issues2 = validate_league("nhl", fetch_nhl_standings, build_nhl_bracket)
    all_issues.extend(issues2)

    # NFL
    ok3, issues3 = validate_league("nfl", fetch_nfl_standings)
    all_issues.extend(issues3)

    # MLB
    ok4, issues4 = validate_league("mlb", fetch_mlb_standings)
    all_issues.extend(issues4)

    ok_final = len(all_issues) == 0
    return ok_final, all_issues


if __name__ == "__main__":
    ok, issues = run_global_validation()

    print("\nRunning global team name validation...\n")

    if ok:
        print("ALL LEAGUES VALID ✓")
    else:
        print("VALIDATION FOUND ISSUES ⚠")
        for i in issues:
            print(i)

    print("\nValidation complete.\n")
