from datetime import datetime, timezone
import dateutil.parser

def is_evening_game(commence_time, cutoff_hour=18):
    """
    Returns True if the game starts at or after 6 PM local time.
    """
    try:
        dt = dateutil.parser.isoparse(commence_time)
        local = dt.astimezone()  # convert to local timezone
        return local.hour >= cutoff_hour
    except Exception:
        return True  # fail open

from engine.edge_calculator import calculate_nrfi_plays, grade_all_props
from engine.prop_generator import generate_k_props
from engine.baseball_batter_props import generate_all_baseball_batter_props


def generate_baseball_slate():
    # NRFI/YRFI (already sorted + top 3 in patched version)
    nrfi = calculate_nrfi_plays(style="ee")

    # Pitcher Ks
    k_raw = generate_k_props()
    k_graded = grade_all_props(k_raw)
    k_top3 = k_graded[:3]

    # Batter props (MLB + KBO + NPB)
    batter_graded = generate_all_baseball_batter_props()

    hits_top3 = [p for p in batter_graded if p["prop_label"] == "HITS"][:3]
    tb_top3 = [p for p in batter_graded if p["prop_label"] == "TOTAL_BASES"][:3]
    hr_top3 = [p for p in batter_graded if p["prop_label"] == "HOME_RUNS"][:3]
    rbi_top3 = [p for p in batter_graded if p["prop_label"] == "RBI"][:3]
    runs_top3 = [p for p in batter_graded if p["prop_label"] == "RUNS"][:3]

    return {
        "nrfi": nrfi,
        "k_props": k_top3,
        "hits": hits_top3,
        "total_bases": tb_top3,
        "home_runs": hr_top3,
        "rbi": rbi_top3,
        "runs": runs_top3,
    }
