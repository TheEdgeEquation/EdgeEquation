from typing import List, Dict
from engine.bracket_core import TeamRecord, assign_seeds_by_conference, build_standard_1_to_6_bracket_with_byes


def build_mlb_bracket(records: List[TeamRecord]) -> Dict[str, Dict]:
    """
    MLB bracket builder (6 teams per league).
    Seeds:
      1 & 2 = byes
      3 vs 6
      4 vs 5
    """

    al = assign_seeds_by_conference(records, "AL", num_seeds=6)
    nl = assign_seeds_by_conference(records, "NL", num_seeds=6)

    return {
        "AL": build_standard_1_to_6_bracket_with_byes(al),
        "NL": build_standard_1_to_6_bracket_with_byes(nl),
    }
