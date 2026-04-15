from dataclasses import dataclass
from typing import List, Dict, Literal, Optional

Sport = Literal["nba", "nhl", "nfl", "mlb"]


@dataclass
class TeamRecord:
    sport: Sport
    team: str
    conference: str          # "East"/"West" or "AFC"/"NFC" etc.
    division: Optional[str]  # optional, used for NFL/MLB/NHL if needed
    wins: int
    losses: int
    ties: int = 0
    seed: Optional[int] = None  # can be pre-assigned if you already know seeds

    @property
    def win_pct(self) -> float:
        games = self.wins + self.losses + self.ties
        if games == 0:
            return 0.0
        return (self.wins + 0.5 * self.ties) / games


def _sort_by_win_pct(records: List[TeamRecord]) -> List[TeamRecord]:
    return sorted(records, key=lambda r: r.win_pct, reverse=True)


def assign_seeds_by_conference(
    records: List[TeamRecord],
    conference: str,
    num_seeds: int,
) -> List[TeamRecord]:
    """
    Take all teams in a conference, sort by win%, assign seeds 1..num_seeds.
    If seeds are already set on records, they are respected and just sorted.
    """
    conf_teams = [r for r in records if r.conference == conference]

    # If seeds already present, just sort by seed
    if all(r.seed is not None for r in conf_teams):
        seeded = sorted(conf_teams, key=lambda r: r.seed)[:num_seeds]
        return seeded

    # Otherwise, sort by win% and assign seeds
    sorted_teams = _sort_by_win_pct(conf_teams)[:num_seeds]
    for i, r in enumerate(sorted_teams, start=1):
        r.seed = i
    return sorted_teams


def build_standard_1_to_8_bracket(
    seeded_teams: List[TeamRecord],
) -> List[Dict[str, str]]:
    """
    Build a standard 1–8 bracket:
      1 vs 8, 2 vs 7, 3 vs 6, 4 vs 5
    Returns list of dicts:
      {"higher_seed": team_name, "lower_seed": team_name, "conference": "..."}
    """
    # Ensure sorted by seed
    seeded_teams = sorted(seeded_teams, key=lambda r: r.seed or 99)
    if len(seeded_teams) != 8:
        raise ValueError("Expected 8 seeded teams for 1–8 bracket")

    by_seed = {r.seed: r for r in seeded_teams}
    pairs = [(1, 8), (2, 7), (3, 6), (4, 5)]

    matchups: List[Dict[str, str]] = []
    conf = seeded_teams[0].conference if seeded_teams else "Unknown"

    for high, low in pairs:
        high_team = by_seed[high].team
        low_team = by_seed[low].team
        matchups.append(
            {
                "higher_seed": high_team,
                "lower_seed": low_team,
                "conference": conf,
            }
        )

    return matchups


def build_standard_1_to_6_bracket_with_byes(
    seeded_teams: List[TeamRecord],
) -> Dict[str, List[Dict[str, str]]]:
    """
    Example for NFL/MLB-style 6-team bracket:
      1 and 2 get byes
      3 vs 6, 4 vs 5 in first round
    Returns dict with:
      {
        "byes": [team1, team2],
        "matchups": [ {higher_seed, lower_seed, conference}, ... ]
      }
    """
    seeded_teams = sorted(seeded_teams, key=lambda r: r.seed or 99)
    if len(seeded_teams) != 6:
        raise ValueError("Expected 6 seeded teams for 1–6 bracket")

    by_seed = {r.seed: r for r in seeded_teams}
    conf = seeded_teams[0].conference if seeded_teams else "Unknown"

    byes = [by_seed[1].team, by_seed[2].team]
    pairs = [(3, 6), (4, 5)]

    matchups: List[Dict[str, str]] = []
    for high, low in pairs:
        matchups.append(
            {
                "higher_seed": by_seed[high].team,
                "lower_seed": by_seed[low].team,
                "conference": conf,
            }
        )

    return {"byes": byes, "matchups": matchups}
