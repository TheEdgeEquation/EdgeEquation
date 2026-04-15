from dataclasses import dataclass
from typing import List, Dict, Literal, Optional

Sport = Literal["nba", "nhl", "nfl", "mlb"]


@dataclass
class TeamRecord:
    sport: Sport
    team: str
    conference: str          # "East"/"West", "AFC"/"NFC", "AL"/"NL"
    division: Optional[str]  # optional
    wins: int
    losses: int
    ties: int = 0
    seed: Optional[int] = None  # can be pre-assigned

    @property
    def win_pct(self) -> float:
        games = self.wins + self.losses + self.ties
        if games == 0:
            return 0.0
        return (self.wins + 0.5 * self.ties) / games


def assign_seeds_by_conference(
    records: List[TeamRecord],
    conference: str,
    num_seeds: int,
) -> List[TeamRecord]:
    conf_teams = [r for r in records if r.conference == conference]

    if all(r.seed is not None for r in conf_teams):
        return sorted(conf_teams, key=lambda r: r.seed)[:num_seeds]

    sorted_teams = sorted(conf_teams, key=lambda r: r.win_pct, reverse=True)[:num_seeds]
    for i, r in enumerate(sorted_teams, start=1):
        r.seed = i
    return sorted_teams


def build_standard_1_to_8_bracket(
    seeded_teams: List[TeamRecord],
) -> List[Dict[str, str]]:
    seeded_teams = sorted(seeded_teams, key=lambda r: r.seed or 99)
    if len(seeded_teams) != 8:
        raise ValueError("Expected 8 seeded teams for 1–8 bracket")

    by_seed = {r.seed: r for r in seeded_teams}
    pairs = [(1, 8), (2, 7), (3, 6), (4, 5)]
    conf = seeded_teams[0].conference if seeded_teams else "Unknown"

    matchups: List[Dict[str, str]] = []
    for high, low in pairs:
        matchups.append(
            {
                "higher_seed": by_seed[high].team,
                "lower_seed": by_seed[low].team,
                "conference": conf,
            }
        )
    return matchups
