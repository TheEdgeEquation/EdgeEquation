# engines/results.py

from datetime import datetime

def get_results():
    """
    Results engine returns a structured summary of yesterday's outcomes.
    Replace with real scraper/model output later.
    """
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "wins": 3,
            "losses": 1,
            "pushes": 0,
        },
        "details": [
            {"pick": "Yankees NRFI", "result": "Win"},
            {"pick": "Dodgers ML", "result": "Win"},
            {"pick": "Rangers TT Over", "result": "Loss"},
            {"pick": "Astros F5 ML", "result": "Win"},
        ]
    }
