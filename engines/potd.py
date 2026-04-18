# engines/potd.py

from datetime import datetime
from core.projections_logger import log_projection


def _select_potd_pick() -> dict:
    """
    Placeholder Prop of the Day selector.
    Later this will pull from your real model.
    """
    return {
        "sport": "NBA",
        "league": "NBA",
        "player": "Anthony Davis",
        "market": "player_rebounds",
        "line": 11.5,
        "side": "over",
        "model_prob": 0.68,
        "edge_ev": 0.21,
        "reason": "Model projects 14.2 rebounds vs undersized frontcourt",
    }


def post_potd():
    """
    Prop of the Day engine entrypoint.
    - Selects pick
    - Logs projection to WAL
    - Returns clean payload for posting engine
    """
    pick = _select_potd_pick()

    projection_payload = {
        "projection_id": f"potd-{pick['sport'].lower()}-{pick['player'].lower().replace(' ', '-')}",
        "timestamp": datetime.utcnow().isoformat() + "Z",

        "sport": pick["sport"],
        "league": pick["league"],
        "game_id": f"{pick['sport'].lower()}-potd-{datetime.utcnow().strftime('%Y%m%d')}",

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

        "mode": "potd",
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
