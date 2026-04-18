# engines/smash.py

from datetime import datetime
from core.projections_logger import log_projection


def _select_smash_pick() -> dict:
    """
    Placeholder Smash selector.
    Later this will pull from your real model.
    """
    return {
        "sport": "MLB",
        "league": "MLB",
        "team": "Dodgers",
        "market": "moneyline",
        "model_prob": 0.67,
        "edge_ev": 0.22,
        "reason": "Elite pitching matchup + bullpen advantage",
    }


def post_smash():
    """
    Smash of the Day engine entrypoint.
    - Selects pick
    - Logs projection to WAL
    - Returns clean payload for posting engine
    """
    pick = _select_smash_pick()

    projection_payload = {
        "projection_id": f"smash-{pick['sport'].lower()}-{pick['team'].lower()}",
        "timestamp": datetime.utcnow().isoformat() + "Z",

        "sport": pick["sport"],
        "league": pick["league"],
        "game_id": f"{pick['sport'].lower()}-smash-{datetime.utcnow().strftime('%Y%m%d')}",

        "home_team": None,
        "away_team": None,
        "start_time": None,

        "market": pick["market"],
        "team": pick["team"],
        "player": None,
        "side": None,
        "line": None,
        "price": None,

        "model_projection": pick["model_prob"],
        "model_prob": pick["model_prob"],
        "edge_ev": pick["edge_ev"],

        "mode": "smash",
        "posted_to_x": False,
    }

    log_projection(projection_payload)

    return {
        "label": f"{pick['team']} ML",
        "sport": pick["sport"],
        "market": pick["market"],
        "team": pick["team"],
        "model_prob": pick["model_prob"],
        "edge_ev": pick["edge_ev"],
        "reason": pick["reason"],
        "timestamp": projection_payload["timestamp"],
    }
