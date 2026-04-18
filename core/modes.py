# core/modes.py
"""
Unified Mode Loader for The Edge Equation.

This file provides:
- Human-readable metadata for every mode
- Categorization for premium vs system modes
- Posting order definitions
- Helper functions for UI, API, CLI, and automation layers

This is the authoritative directory of all modes.
"""

from typing import Dict, Any, List


# ---------------------------------------------------------------------------
# Mode Metadata
# ---------------------------------------------------------------------------

MODES_INFO: Dict[str, Dict[str, Any]] = {

    # -----------------------------------------------------------------------
    # Premium Daily Modes
    # -----------------------------------------------------------------------

    "spotlight": {
        "name": "Spotlight Insight",
        "category": "premium",
        "description": "High-confidence player prop with elite model alignment.",
        "emoji": "🔦",
        "order": 1,
        "active": True,
    },

    "smash": {
        "name": "Smash of the Day",
        "category": "premium",
        "description": "Top model-backed team-side play with strong EV.",
        "emoji": "💥",
        "order": 2,
        "active": True,
    },

    "outlier": {
        "name": "Outlier of the Day",
        "category": "premium",
        "description": "Largest model-vs-market gap on the slate.",
        "emoji": "📈",
        "order": 3,
        "active": True,
    },

    "sharp": {
        "name": "Sharp Signal",
        "category": "premium",
        "description": "Model + matchup + movement all point the same direction.",
        "emoji": "📊",
        "order": 4,
        "active": True,
    },

    "potd": {
        "name": "Prop of the Day",
        "category": "premium",
        "description": "Flagship cross-sport prop with high model confidence.",
        "emoji": "🎯",
        "order": 5,
        "active": True,
    },

    "gotd": {
        "name": "Game of the Day",
        "category": "premium",
        "description": "Full-game breakdown with matchup context and EV.",
        "emoji": "🏆",
        "order": 6,
        "active": True,
    },

    "fipotd": {
        "name": "First Inning Prop of the Day",
        "category": "premium",
        "description": "MLB-specific NRFI/YRFI model-driven early-game edge.",
        "emoji": "⏱️",
        "order": 7,
        "active": True,
    },

    # -----------------------------------------------------------------------
    # System Modes
    # -----------------------------------------------------------------------

    "edges": {
        "name": "Edges Board",
        "category": "system",
        "description": "Full slate of model-qualified edges.",
        "emoji": "📊",
        "order": None,
        "active": True,
    },

    "facts": {
        "name": "Facts Mode",
        "category": "system",
        "description": "Data-only slate insights and trend facts.",
        "emoji": "📚",
        "order": None,
        "active": True,
    },

    "results": {
        "name": "Results Mode",
        "category": "system",
        "description": "Full premium results breakdown with EV delta.",
        "emoji": "📌",
        "order": None,
        "active": True,
    },
}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def list_modes() -> List[Dict[str, Any]]:
    """
    Return all modes with metadata.
    """
    return [
        {"key": key, **info}
        for key, info in MODES_INFO.items()
        if info.get("active", True)
    ]


def get_mode_info(mode_name: str) -> Dict[str, Any]:
    """
    Return metadata for a single mode.
    """
    mode_name = mode_name.lower().strip()
    if mode_name not in MODES_INFO:
        raise ValueError(f"Unknown mode: {mode_name}")
    return MODES_INFO[mode_name]


def get_premium_modes() -> List[str]:
    """
    Return a list of premium mode keys in posting order.
    """
    premium = [
        (key, info["order"])
        for key, info in MODES_INFO.items()
        if info["category"] == "premium" and info.get("active", True)
    ]
    premium_sorted = sorted(premium, key=lambda x: x[1])
    return [key for key, _ in premium_sorted]


def get_system_modes() -> List[str]:
    """
    Return a list of system mode keys.
    """
    return [
        key for key, info in MODES_INFO.items()
        if info["category"] == "system" and info.get("active", True)
    ]


def get_daily_posting_order() -> List[str]:
    """
    Return the deterministic posting order for daily premium modes.
    """
    return get_premium_modes()


def is_mode_active(mode_name: str) -> bool:
    """
    Check if a mode is active.
    """
    return MODES_INFO.get(mode_name, {}).get("active", False)
