from typing import List, Dict
from engine.bracket_core import TeamRecord
from engine.odds_api_client import (
    fetch_nba_standings,
    fetch_nhl_standings,
    fetch_nfl_standings,
    fetch_mlb_standings,
)
from engine.standings_to_records import convert_to_team_records
from engine.nba_bracket import build_nba_bracket
from engine.nhl_bracket import build_nhl_bracket


def get_nba_playoff_matchups() -> List[Dict[str, str]]:
    standings = fetch_nba_standings()
    records = convert_to_team_records(standings, sport="nba")
    return build_nba_bracket(records)


def get_nhl_playoff_matchups() -> List[Dict[str, str]]:
    standings = fetch_nhl_standings()
    records = convert_to_team_records(standings, sport="nhl")
    return build_nhl_bracket(records)


# NFL + MLB scaffolds (ready when you extend the engine)

def get_nfl_playoff_structure():
    standings = fetch_nfl_standings()
    records = convert_to_team_records(standings, sport="nfl")
    # TODO: build NFL bracket (7-team per conference) when you’re ready
    return records


def get_mlb_playoff_structure():
    standings = fetch_mlb_standings()
    records = convert_to_team_records(standings, sport="mlb")
    # TODO: build MLB bracket (6-team per league with byes) when you’re ready
    return records
