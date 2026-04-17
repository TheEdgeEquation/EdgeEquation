# engines/edges.py

"""
Edges Engine
------------
Provides structured data for:
- edges_morning
- edges_evening

Formatters expect:
{
    "timestamp": "...",
    "edges": [
        {"team": "...", "edge": "...", "confidence": 0.0},
        ...
    ]
}
"""

from datetime import datetime

def _edge(team, edge, confidence):
    """Simple deterministic placeholder edge record."""
    return {
        "team": team,
        "edge": edge,
        "confidence": confidence,
    }

def get_morning_edges():
    """
    Returns structured morning edges data.
    Replace with real model output later.
    """
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "edges": [
            _edge("Yankees", "Pitching edge vs LHP", 0.62),
            _edge("Dodgers", "Bullpen advantage", 0.58),
            _edge("Rangers", "Lineup vs RHP", 0.55),
        ]
    }

def get_evening_edges():
    """
    Returns structured evening edges data.
    Replace with real model output later.
    """
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "edges": [
            _edge("Padres", "Late-game bullpen edge", 0.60),
            _edge("Astros", "Matchup vs LHP", 0.57),
            _edge("Braves", "Power index advantage", 0.59),
        ]
    }
