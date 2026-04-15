from typing import List, Dict
from engine.bracket_core import TeamRecord, assign_seeds_by_conference, build_standard_1_to_8_bracket


def build_nba_bracket_from_records(records: List[TeamRecord]) -> List[Dict[str, str]]:
    """
    records: full-season NBA records with conference set ("East"/"West").
    Assumes Play-In is already resolved and these are the final 8 per conference,
    OR you pass all teams and let this function take the top 8 by win%.
    """
    east_seeds = assign_seeds_by_conference(records, "East", num_seeds=8)
    west_seeds = assign_seeds_by_conference(records, "West", num_seeds=8)

    east_bracket = build_standard_1_to_8_bracket(east_seeds)
    west_bracket = build_standard_1_to_8_bracket(west_seeds)

    return east_bracket + west_bracket
