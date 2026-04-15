"""
Global Team Name Validator
--------------------------

This script checks for:
  - Team name mismatches between Odds API standings
  - Team names used in your playoff engine
  - Team names used in your TEAM_STRENGTH dictionaries
  - Team names used in bracket generation
  - Team names used in posting/formatting

Run with:
    python validate_teams.py

If ANY mismatch exists, it will be printed clearly.
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


def extract_team_names_from_odds_api(fetch_func, sport):
    try:
        raw = fetch_func()
        records = convert_to_team_records(raw, sport=sport)
        return {r.team for r in records}
    except Exception as e:
        print(f"[ERROR] Failed fetching {sport.upper()} standings:")
        print(e)
        return set()


def extract_team_names_from_strength_dict():
    return set(TEAM_STRENGTH.keys())


def validate_league(league_name, fetch_func, bracket_builder=None):
    print("\n" + "=" * 80)
    print(f"VALIDATING {league_name.upper()}")
    print("=" * 80)

    # 1. Odds API names
    odds_names = extract_team_names_from_odds_api(fetch_func, league_name)
    print(f"\nOdds API returned {len(odds_names)} teams.")

    # 2. Model dictionary names
    model_names = extract_team_names_from_strength_dict()
    print(f"Model strength dict contains {len(model_names)} teams.")

    # 3. Bracket names (if applicable)
    bracket_names = set()
    if bracket_builder:
        try:
            raw = fetch_func()
            records = convert_to_team_records(raw, sport=league_name)
            matchups = bracket_builder(records)
            for m in matchups:
                bracket_names.add(m["higher_seed"])
                bracket_names.add(m["lower_seed"])
            print(f"Bracket builder produced {len(bracket_names)} unique teams.")
        except Exception as e:
            print(f"[ERROR] Bracket builder failed for {league_name}:")
            print(e)

    # -------------------------
    # VALIDATION
    # -------------------------

    print("\nChecking for mismatches...")

    # Odds API vs Model
    missing_in_model = odds_names - model_names
    missing_in_odds = model_names - odds_names

    if missing_in_model:
        print("\n[WARNING] Teams in Odds API but NOT in model strength dict:")
        pprint(missing_in_model)

    if missing_in_odds:
        print("\n[WARNING] Teams in model strength dict but NOT in Odds API:")
        pprint(missing_in_odds)

    # Bracket vs Model
    if bracket_names:
        missing_in_model_from_bracket = bracket_names - model_names
        if missing_in_model_from_bracket:
            print("\n[WARNING] Teams in bracket but NOT in model strength dict:")
            pprint(missing_in_model_from_bracket)

    # Bracket vs Odds API
    if bracket_names:
        missing_in_odds_from_bracket = bracket_names - odds_names
        if missing_in_odds_from_bracket:
            print("\n[WARNING] Teams in bracket but NOT in Odds API standings:")
            pprint(missing_in_odds_from_bracket)

    # Final summary
    if (
        not missing_in_model
        and not missing_in_odds
        and (not bracket_names or (
            not missing_in_model_from_bracket
            and not missing_in_odds_from_bracket
        ))
    ):
        print(f"\n{league_name.upper()} VALIDATION PASSED ✓")
    else:
        print(f"\n{league_name.upper()} VALIDATION FOUND ISSUES ⚠")


if __name__ == "__main__":
    print("\nRunning global team name validation...\n")

    # NBA
    validate_league("nba", fetch_nba_standings, build_nba_bracket)

    # NHL
    validate_league("nhl", fetch_nhl_standings, build_nhl_bracket)

    # NFL (future)
    validate_league("nfl", fetch_nfl_standings)

    # MLB (future)
    validate_league("mlb", fetch_mlb_standings)

    print("\nValidation complete.\n")
