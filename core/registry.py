# core/registry.py
"""
Central Mode Registry for The Edge Equation.

This file provides:
- A single source of truth for all mode runners
- A clean interface for automation and scheduling
- Deterministic routing for every posting mode

Usage:
    from core.registry import run_mode
    run_mode("spotlight")
"""

from typing import Callable, Dict

# Import all mode runners
from modes.spotlight.run import run as spotlight_run
from modes.smash.run import run as smash_run
from modes.outlier.run import run as outlier_run
from modes.sharp.run import run as sharp_run
from modes.potd.run import run as potd_run
from modes.gotd.run import run as gotd_run
from modes.fipotd.run import run as fipotd_run

# System modes
from modes.edges.run import run as edges_run
from modes.facts.run import run as facts_run
from modes.results.run import run as results_run


# ---------------------------------------------------------------------------
# Mode Registry
# ---------------------------------------------------------------------------

MODES: Dict[str, Callable[[], None]] = {
    # Premium Daily Modes
    "spotlight": spotlight_run,
    "smash": smash_run,
    "outlier": outlier_run,
    "sharp": sharp_run,
    "potd": potd_run,
    "gotd": gotd_run,
    "fipotd": fipotd_run,

    # System Modes
    "edges": edges_run,
    "facts": facts_run,
    "results": results_run,
}


# ---------------------------------------------------------------------------
# Public Interface
# ---------------------------------------------------------------------------

def run_mode(mode_name: str) -> None:
    """
    Run any registered mode by name.

    Raises:
        ValueError: if the mode is not registered.
    """
    mode_name = mode_name.lower().strip()

    if mode_name not in MODES:
        raise ValueError(f"Unknown mode: '{mode_name}'. "
                         f"Available modes: {', '.join(MODES.keys())}")

    runner = MODES[mode_name]
    runner()
