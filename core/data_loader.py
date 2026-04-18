# core/data_loader.py
"""
Data Loader Contracts for The Edge Equation.

This file defines the canonical interfaces and schemas expected by:
- premium mode engines (Spotlight, Smash, Outlier, Sharp, POTD, GOTD, FIPOTD)
- system modes (Edges, Facts, Results)

Implementations are up to you (DB, CSV, API, etc.).
The engines rely ONLY on these shapes.
"""

from typing import List, Dict, Any


# ---------------------------------------------------------------------------
# Props Loader
# ---------------------------------------------------------------------------

def load_props() -> List[Dict[str, Any]]:
    """
    Return a list of player prop dicts.

    Each prop MUST expose at least:

    {
        "player": str,
        "sport": str,          # e.g. "MLB", "NBA"
        "market": str,         # e.g. "PTS", "RBI", "NRFI", "YRFI"
        "line": float | int | str,
        "side": str,           # "over" / "under" / "yes" / "no"
        "model_prob": float,   # 0.0–1.0
        "edge_ev": float,      # expected value in units
        "reason": str | None,  # short explanation
        "home_team": str | None,
        "away_team": str | None,
    }

    You can include extra fields; engines will ignore what they don't use.
    """
    raise NotImplementedError("Implement load_props() to return a list of prop dicts.")


# ---------------------------------------------------------------------------
# Games Loader
# ---------------------------------------------------------------------------

def load_games() -> List[Dict[str, Any]]:
    """
    Return a list of game-level dicts.

    Each game MUST expose at least:

    {
        "sport": str,          # e.g. "MLB", "NBA", "NFL"
        "home_team": str,
        "away_team": str,
        "team": str | None,    # side we are backing (for Smash/GOTD/Sharp)
        "side": str | None,    # e.g. "-1.5", "+3.5", "ML"
        "market": str,         # e.g. "spread", "moneyline", "total"
        "model_prob": float,   # 0.0–1.0
        "edge_ev": float,      # expected value in units
        "reason": str | None,  # short explanation
        "context": str | None, # matchup context for GOTD
    }

    Extra fields are allowed.
    """
    raise NotImplementedError("Implement load_games() to return a list of game dicts.")


# ---------------------------------------------------------------------------
# Edges Loader
# ---------------------------------------------------------------------------

def load_edges() -> List[Dict[str, Any]]:
    """
    Return a list of edges for Edges Mode.

    Each edge dict SHOULD expose:

    {
        "label": str,          # human-readable label (team/player + market)
        "sport": str,
        "market": str,
        "model_prob": float | None,
        "edge_ev": float | None,
        "reason": str | None,
    }

    The formatter is tolerant, but these fields unlock the full experience.
    """
    raise NotImplementedError("Implement load_edges() to return a list of edge dicts.")


# ---------------------------------------------------------------------------
# Facts Loader
# ---------------------------------------------------------------------------

def load_facts() -> List[str]:
    """
    Return a list of short, sharp fact strings for Facts Mode.

    Example:
        [
            "Team X is 12–3 vs LHP since June.",
            "Player Y has cleared 2.5 threes in 8 of last 10.",
        ]
    """
    raise NotImplementedError("Implement load_facts() to return a list of fact strings.")


# ---------------------------------------------------------------------------
# Results Loader
# ---------------------------------------------------------------------------

def load_results() -> Dict[str, Any]:
    """
    Return a dict with full results payload for Results Mode.

    Expected shape:

    {
        "date": "YYYY-MM-DD",
        "results": [
            {
                "label": str,          # e.g. "Player X o2.5 3PM"
                "sport": str,
                "market": str,
                "result": str,         # "hit" | "miss" | "push"
                "model_prob": float | None,
                "edge_ev": float | None,
                "final_score": str | None,  # e.g. "3 vs line 2.5"
                "ev_delta": float | None,   # realized EV vs expectation
            },
            ...
        ],
        "summary": {
            "total_picks": int,
            "hits": int,
            "misses": int,
            "pushes": int | None,
            "accuracy": float | None,       # 0–100
            "total_ev_delta": float | None, # total realized EV
            "best_pick_label": str | None,
            "worst_pick_label": str | None,
        },
    }
    """
    raise NotImplementedError("Implement load_results() to return a results payload dict.")
