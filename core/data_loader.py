# core/data_loader.py
"""
Temporary test data loader for validation.

This gives the engines known-good, hard-coded data so we can
verify formatting, posting, logging, and failsafe behavior
without worrying about upstream feeds yet.
"""

from typing import List, Dict, Any


def load_props() -> List[Dict[str, Any]]:
    return [
        {
            "player": "Test Player",
            "sport": "MLB",
            "market": "RBI",
            "line": 0.5,
            "side": "over",
            "model_prob": 0.64,
            "edge_ev": 0.35,
            "reason": "Model likes matchup vs RHP.",
            "home_team": "Home Team",
            "away_team": "Away Team",
        }
    ]


def load_games() -> List[Dict[str, Any]]:
    return [
        {
            "sport": "MLB",
            "home_team": "Home Team",
            "away_team": "Away Team",
            "team": "Home Team",
            "side": "ML",
            "market": "moneyline",
            "model_prob": 0.61,
            "edge_ev": 0.40,
            "reason": "Bullpen edge + starter advantage.",
            "context": "Division matchup, weather neutral.",
        }
    ]


def load_edges() -> List[Dict[str, Any]]:
    return [
        {
            "label": "Home Team ML",
            "sport": "MLB",
            "market": "moneyline",
            "model_prob": 0.61,
            "edge_ev": 0.40,
            "reason": "Model vs market gap.",
        }
    ]


def load_facts() -> List[str]:
    return [
        "Home Team is 8–2 in last 10 vs RHP.",
        "Test Player has cleared 0.5 RBI in 6 of last 9.",
    ]


def load_results() -> Dict[str, Any]:
    return {
        "date": "2026-04-17",
        "results": [
            {
                "label": "Test Player o0.5 RBI",
                "sport": "MLB",
                "market": "RBI",
                "result": "hit",
                "model_prob": 0.64,
                "edge_ev": 0.35,
                "final_score": "1 RBI vs line 0.5",
                "ev_delta": 0.50,
            }
        ],
        "summary": {
            "total_picks": 1,
            "hits": 1,
            "misses": 0,
            "pushes": 0,
            "accuracy": 100.0,
            "total_ev_delta": 0.50,
            "best_pick_label": "Test Player o0.5 RBI",
            "worst_pick_label": None,
        },
    }
