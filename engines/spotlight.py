# engines/spotlight.py

from core.projections_logger import log_projection
from datetime import datetime


from datetime import datetime

def get_spotlight():
    """
    Spotlight engine returns a single cross-sport highlight pick.
    """
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sport": "NBA",
        "player": "Luka Doncic",
        "prop": "Over 8.5 assists",
        "confidence": 0.63,
        "reason": "High usage rate vs weak perimeter defense",
    }
