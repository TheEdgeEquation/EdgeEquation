from engine.results_loader import get_todays_graded_plays
from engine.results_checker import (
    check_mlb_results,
    check_pitcher_results,
    check_global_results,
)
from engine.global_accuracy import evaluate_global_results


def compute_full_accuracy():
    """
    Returns a dictionary with:
    - internal accuracy (all projections)
    - public accuracy (posted picks only)
    """

    todays_plays = get_todays_graded_plays() or []

    # -----------------------------
    # INTERNAL ACCURACY
    # -----------------------------
    mlb_game_projs = [
        p for p in todays_plays
        if p.get("sport") == "baseball_mlb"
        and p.get("prop_label") not in ("K", "NRFI", "YRFI")
    ]

    pitcher_projs = [
        p for p in todays_plays
        if p.get("prop_label") == "K"
    ]

    nrfi_projs = [
        p for p in todays_plays
        if p.get("prop_label") in ("NRFI", "YRFI")
    ]

    global_plays = [
        p for p in todays_plays
        if p.get("sport") in ("kbo", "npb", "soccer_epl", "soccer_ucl")
    ]

    game_hits, game_misses = check_mlb_results(mlb_game_projs)
    pitcher_hits, pitcher_misses = check_pitcher_results(pitcher_projs)
    nrfi_hits, nrfi_misses = check_mlb_results(nrfi_projs)

    global_stats = evaluate_global_results(global_plays)

    internal = {
        "mlb_games": (len(game_hits), len(game_misses)),
        "pitchers": (len(pitcher_hits), len(pitcher_misses)),
        "nrfi": (len(nrfi_hits), len(nrfi_misses)),
        "global": global_stats,
    }

    # -----------------------------
    # PUBLIC ACCURACY
    # -----------------------------
    # For now, public accuracy = same as internal until we tag public picks.
    # You can refine this once public picks are tagged in the DB.
    public = internal.copy()

    return internal, public
