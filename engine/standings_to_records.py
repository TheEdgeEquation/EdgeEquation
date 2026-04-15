from typing import List, Dict, Any
from engine.bracket_core import TeamRecord, Sport


def convert_to_team_records(
    standings: List[Dict[str, Any]],
    sport: Sport,
    conference_key: str = "conference",
    division_key: str = "division",
    team_key: str = "team",
    wins_key: str = "wins",
    losses_key: str = "losses",
    ties_key: str = "ties",
) -> List[TeamRecord]:
    records: List[TeamRecord] = []
    for row in standings:
        records.append(
            TeamRecord(
                sport=sport,
                team=row[team_key],
                conference=row[conference_key],
                division=row.get(division_key),
                wins=int(row[wins_key]),
                losses=int(row[losses_key]),
                ties=int(row.get(ties_key, 0)),
            )
        )
    return records
