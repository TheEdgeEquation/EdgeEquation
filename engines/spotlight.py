# engines/spotlight.py

from datetime import datetime
from core.projections_logger import log_projection


def _select_spotlight_pick() -> dict:
    """
    Placeholder spotlight selector.
    Later this will pull from your real model.
    """
    return {
        "sport": "NBA",
        "league": "NBA",
        "player": "Luka Doncic",
        "market": "player_assists",
        "line": 8.5,
        "side": "over",
        "model_prob": 0.63,
        "edge_ev": 0.18,
        "reason": "High usage rate vs weak perimeter defense",
    }


def post_spotlight():
    """
    Main Spotlight engine entrypoint.
    - Selects spotlight pick
    - Logs projection to WAL
    - Returns a clean payload for posting engine
    """
    pick = _select_spotlight_pick()

    projection_payload = {
        "projection_id": f"spotlight-{pick['sport'].lower()}-{pick['player'].lower().replace(' ', '-')}",
        "timestamp": datetime.utcnow().isoformat() + "Z",

        "sport": pick["sport"],
        "league": pick["league"],
        "game_id": f"{pick['sport'].lower()}-spotlight-{datetime.utcnow().strftime('%Y%m%d')}",

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

        "mode": "spotlight",
        "posted_to_x": False,
    }

    # Log to WAL
    log_projection(projection_payload)

    # Return payload for posting engine
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
