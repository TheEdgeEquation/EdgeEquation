from typing import List, Dict, Any


def fetch_nba_standings() -> List[Dict[str, Any]]:
    """
    TODO: Implement using The Odds API.
    Should return a list of dicts like:
      {
        "team": "Boston Celtics",
        "conference": "East",
        "division": "Atlantic",
        "wins": 64,
        "losses": 18,
        "ties": 0,
      }
    """
    raise NotImplementedError("Wire this to The Odds API standings endpoint for NBA")


def fetch_nhl_standings() -> List[Dict[str, Any]]:
    """
    TODO: Implement using The Odds API for NHL.
    """
    raise NotImplementedError("Wire this to The Odds API standings endpoint for NHL")


def fetch_nfl_standings() -> List[Dict[str, Any]]:
    """
    TODO: Implement using The Odds API for NFL.
    """
    raise NotImplementedError("Wire this to The Odds API standings endpoint for NFL")


def fetch_mlb_standings() -> List[Dict[str, Any]]:
    """
    TODO: Implement using The Odds API for MLB.
    """
    raise NotImplementedError("Wire this to The Odds API standings endpoint for MLB")
