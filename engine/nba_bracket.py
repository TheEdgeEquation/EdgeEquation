from typing import List, Dict
from engine.bracket_core import TeamRecord, assign_seeds_by_conference, build_standard_1_to_8_bracket


def build_nba_bracket(records: List[TeamRecord]) -> List[Dict[str, str]]:
    """
    Assumes:
      - Play-In is resolved
      - records contain either full standings or just playoff teams
    """
    east = assign_seeds_by_conference(records, "East", num_seeds=8)
    west = assign_seeds_by_conference(records, "West", num_seeds=8)

    east_bracket = build_standard_1_to_8_bracket(east)
    west_bracket = build_standard_1_to_8_bracket(west)

    return east_bracket + west_bracket
