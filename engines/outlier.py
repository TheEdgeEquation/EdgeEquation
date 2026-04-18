# engines/outlier.py

from datetime import datetime
from core.projections_logger import log_projection


def _select_outlier_pick() -> dict:
    """
    Placeholder Outlier selector.
    Later this will pull from your real model.
    """
    return {
        "sport": "NBA",
        "league": "NBA",
        "player": "Shai Gilgeous-Alexander",
        "market": "player_points",
        "line": 27.5,
        "side": "over",
        "model_prob": 0.71,
        "edge_ev": 0.28,
        "reason": "Model projects 32.1 points vs a soft interior defense",
    }


def post_outlier():
    """
    Outlier of the Day engine entrypoint.
    - Selects pick
    - Logs projection to WAL
    - Returns clean payload for posting engine
    """
    pick = _select_outlier_pick()

    projection_payload = {
        "projection_id": f"outlier-{pick['sport'].lower()}-{pick['player'].lower().replace(' ', '-')}",
        "timestamp": datetime.utcnow().isoformat() + "Z",

        "sport": pick["sport"],
        "league": pick["league"],
        "game_id": f"{pick['sport'].lower()}-outlier-{datetime.utcnow().strftime('%Y%m%d')}",

        "home_team": None,
        "away_team": None,
        "start_time": None,

        "market": pick["market"],
        "team": None,
        "player": pick["player"],
        "side": pick["side"],
        "line": pick["line"],
        "price": None,

        "model_projection": pick["model_prob"],
        "model_prob": pick["model_prob"],
        "edge_ev": pick["edge_ev"],

        "mode": "outlier",
        "posted_to_x": False,
    }

    log_projection(projection_payload)

    return {
        "label": f"{pick['player']} — {pick['side'].upper()} {pick['line']}",
        "sport": pick["sport"],
        "market": pick["market"],
        "player": pick["player"],
        "line": pick["line"],
        "side": pick["side"],
        "model_prob": pick["model_prob"],
        "edge_ev": pick["edge_ev"],
        "reason": pick["reason"],
        "timestamp": projection_payload["timestamp"],
    }
