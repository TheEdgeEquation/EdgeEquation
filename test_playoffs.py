"""
Test script for verifying:
  - Odds API standings adapters
  - TeamRecord conversion
  - Automatic bracket generation
  - Playoff series projections
  - Formatting layer

Run with:
    python test_playoffs.py
"""

from pprint import pprint

# Bracket + standings adapters
from engine.bracket_auto import (
    get_nba_playoff_matchups,
    get_nhl_playoff_matchups,
)

# Playoff engine + formatting
from engine.playoff_engine import project_series
from engine.playoff_formatter import format_league_overview, format_all_matchups


def test_league(league_name: str, get_matchups_func):
    print("\n" + "=" * 80)
    print(f"TESTING {league_name.upper()} PLAYOFF AUTOMATION")
    print("=" * 80)

    try:
        matchups = get_matchups_func()
    except Exception as e:
        print(f"[ERROR] Failed to generate {league_name} matchups:")
        print(e)
        return

    print("\nGenerated Matchups:")
    pprint(matchups)

    # Validate structure
    for m in matchups:
        for key in ("higher_seed", "lower_seed", "conference"):
            if key not in m:
                print(f"[ERROR] Missing key '{key}' in matchup: {m}")
                return

    print("\nMatchup structure OK.")

    # Run projections
    projections = []
    for m in matchups:
        try:
            proj = project_series(
                higher_seed=m["higher_seed"],
                lower_seed=m["lower_seed"],
                conference=m["conference"],
                sport=league_name,
            )
            projections.append(proj)
        except Exception as e:
            print(f"[ERROR] Failed projecting series for matchup {m}:")
            print(e)
            return

    print("\nSeries projections OK.")

    # Format posts
    try:
        overview = format_league_overview(league_name)
        posts = format_all_matchups(projections)
    except Exception as e:
        print(f"[ERROR] Formatting failed for {league_name}:")
        print(e)
        return

    print("\nOverview Post:")
    print(overview)

    print("\nMatchup Posts:")
    for p in posts:
        print("-" * 40)
        print(p)

    print(f"\n{league_name.upper()} TEST COMPLETE ✓")


if __name__ == "__main__":
    print("\nRunning playoff automation tests...\n")

    # Test NBA
    test_league("nba", get_nba_playoff_matchups)

    # Test NHL
    test_league("nhl", get_nhl_playoff_matchups)

    print("\nAll tests finished.\n")
