"""
_mocks/test_graphic.py
Generates both EE and CBC graphics using mock data.
No API keys needed.
Run from repo root: python _mocks/test_graphic.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from _mocks.mock_props import MOCK_PLAYS
from engine.visualizer import (
    generate_main_graphic,
    generate_announce_graphic,
    generate_results_graphic,
    generate_cbc_tease_graphic,
    generate_weekly_graphic,
)

def main():
    print("Generating test graphics using mock data...")

    path = generate_main_graphic(MOCK_PLAYS, style="ee")
    print(f"  ✓ EE daily:      {path}")

    path = generate_main_graphic(MOCK_PLAYS, style="cbc")
    print(f"  ✓ CBC drop:      {path}")

    games = [
        {"sport_label": "MLB", "home": "LAD", "away": "ARI", "time": "2:10 PM"},
        {"sport_label": "NBA", "home": "GSW", "away": "HOU", "time": "7:30 PM"},
        {"sport_label": "NHL", "home": "COL", "away": "VGK", "time": "8:00 PM"},
    ]
    path = generate_announce_graphic(games, style="ee")
    print(f"  ✓ EE announce:   {path}")

    path = generate_cbc_tease_graphic()
    print(f"  ✓ CBC tease:     {path}")

    results = []
    for i, p in enumerate(MOCK_PLAYS):
        r = dict(p)
        r["hit"] = i % 2 == 0
        results.append(r)

    path = generate_results_graphic(results, style="ee")
    print(f"  ✓ EE results:    {path}")

    path = generate_results_graphic(results, style="cbc")
    print(f"  ✓ CBC results:   {path}")

    stats = {
        "total": 14, "hits": 11, "misses": 3,
        "win_rate": 78.6, "units": 8.0,
        "best_play": "Corbin Burnes OVER 7.5 K ✓",
        "worst_play": "MacKinnon OVER 3.5 SOG ✗",
        "week_label": "Apr 7 – Apr 13, 2025",
    }
    path = generate_weekly_graphic(stats)
    print(f"  ✓ Weekly:        {path}")

    print("\nAll graphics saved to output/")

if __name__ == "__main__":
    main()
