import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from _mocks.mock_props import MOCK_PLAYS
from engine.visualizer import (
    generate_main_graphic,
    generate_announce_graphic,
    generate_results_graphic,
    generate_cbc_tease_graphic,
    generate_weekly_graphic,
)

print("Generating preview graphics...")

path = generate_main_graphic(MOCK_PLAYS, style="ee")
print(f"EE daily: {path}")

path = generate_main_graphic(MOCK_PLAYS, style="cbc")
print(f"CBC drop: {path}")

results = []
for i, p in enumerate(MOCK_PLAYS):
    r = dict(p)
    r["hit"] = i % 2 == 0
    results.append(r)

path = generate_results_graphic(results, style="ee")
print(f"EE results: {path}")

print("Done! Check output/ folder.")
