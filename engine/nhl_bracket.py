from typing import List, Dict
from engine.bracket_core import TeamRecord, build_standard_1_to_8_bracket


def build_nhl_bracket(records: List[TeamRecord]) -> List[Dict[str, str]]:
    """
    Simplified NHL bracket builder.
    Assumes:
      - records already contain the 8 playoff teams per conference
      - seeds already assigned (1–8)
    """

    east = [r for r in records if r.conference == "East"]
    west = [r for r in records if r.conference == "West"]

    east_bracket = build_standard_1_to_8_bracket(east)
    west_bracket = build_standard_1_to_8_bracket(west)

    return east_bracket + west_bracket
