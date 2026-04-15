from typing import List, Dict
from engine.bracket_core import TeamRecord, assign_seeds_by_conference


def build_nfl_bracket(records: List[TeamRecord]) -> Dict[str, List[Dict[str, str]]]:
    """
    NFL bracket builder (7 teams per conference).
    Seeds:
      1 = bye
      2 vs 7
      3 vs 6
      4 vs 5
    """

    afc = assign_seeds_by_conference(records, "AFC", num_seeds=7)
    nfc = assign_seeds_by_conference(records, "NFC", num_seeds=7)

    def build_conf(seeds):
        return {
            "bye": seeds[0].team,
            "matchups": [
                {"higher_seed": seeds[1].team, "lower_seed": seeds[6].team, "conference": seeds[0].conference},
                {"higher_seed": seeds[2].team, "lower_seed": seeds[5].team, "conference": seeds[0].conference},
                {"higher_seed": seeds[3].team, "lower_seed": seeds[4].team, "conference": seeds[0].conference},
            ]
        }

    return {
        "AFC": build_conf(afc),
        "NFC": build_conf(nfc),
    }
