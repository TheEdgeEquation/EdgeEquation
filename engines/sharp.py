# engines/sharp.py

from datetime import datetime
from core.projections_logger import log_projection


def _select_sharp_pick() -> dict:
    """
    Placeholder Sharp Signal selector.
    Later this will pull from your real model + line movement.
    """
    return {
        "sport": "MLB",
        "league": "MLB",
        "team": "Braves",
        "market": "runline",
        "side": "-1.5",
        "model_prob": 0.64,
        "edge_ev": 0.19,
        "reason": "Model alignment + favorable pitching split + early sharp movement",
    }


def post_sharp():
    """
    Sharp Signal engine entrypoint.
    - Selects pick
    - Logs projection to WAL
    - Returns clean payload for posting engine
    """
    pick = _select_sharp_pick()

    projection_payload = {
        "projection_id": f"sharp-{pick['sport'].lower()}-{pick['team'].lower()}",
        "timestamp": datetime.utcnow().isoformat() + "Z",

        "sport": pick["sport"],
        "league": pick["league"],
        "game_id": f"{pick['sport'].lower()}-sharp-{datetime.utcnow().strftime('%Y%m%d')}",

        "home_team": None,
        "away_team": None,
        "start_time": None,

        "market": pick["market"],
        "team": pick["team"],
        "player": None,
        "side": pick["side"],
        "line": None,
        "price": None,

        "model_projection": pick["model_prob"],
        "model_prob": pick["model_prob"],
        "edge_ev": pick["edge_ev"],

        "mode": "sharp",
        "posted_to_x": False,
    }

    log_projection(projection_payload)

    return {
        "label": f"{pick['team']} {pick['side']}",
        "sport": pick["sport"],
        "market": pick["market"],
        "team": pick["team"],
        "side": pick["side"],
        "model_prob": pick["model_prob"],
        "edge_ev": pick["edge_ev"],
        "reason": pick["reason"],
        "timestamp": projection_payload["timestamp"],
    }
