# picks.py

from dataclasses import dataclass
from typing import List

@dataclass
class Pick:
    label: str          # e.g. "NRFI", "HR Prop", "Smash of the Day"
    matchup: str        # e.g. "LAD @ SF"
    player: str | None  # e.g. "Mookie Betts" or None for NRFI
    line: str           # e.g. "+350", "-120"
    note: str | None    # short context

def load_today_picks() -> List[Pick]:
    # TEMP: hard-coded example; later you can wire this to your real engine
    return [
        Pick("NRFI", "LAD @ SF", None, "-115", "Both starters top-20 in xFIP"),
        Pick("HR Prop", "ATL @ NYM", "Matt Olson", "+340", "Pull-side flyball matchup"),
        Pick("Smash of the Day", "HOU @ TEX", "Yordan Alvarez", "+210", "Barrel rate vs RHP"),
    ]

def validate_picks(picks: List[Pick]) -> None:
    if not picks:
        raise ValueError("No picks loaded for today.")
    labels = [p.label for p in picks]
    if len(labels) != len(set(labels)):
        raise ValueError("Duplicate pick labels detected.")
