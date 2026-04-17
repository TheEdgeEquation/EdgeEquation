import logging
from engine.utils import game_has_started
from engine.content_generators import generate_gotd_from_play, generate_potd_from_play
from engine.edge_calculator import grade_all_props, calculate_nrfi_plays
from engine.prizepicks_scraper import fetch_prizepicks_props

logger = logging.getLogger(__name__)

def run_global_high_confidence_outlier():
    logger.info("MODE: global_high_confidence_outlier")

    props = fetch_prizepicks_props() or []
    graded = grade_all_props(props)
    nrfi = calculate_nrfi_plays() or []
    plays = graded + nrfi

    plays = [
        p for p in plays
        if p.get("sport") in ("kbo", "npb", "soccer_epl", "soccer_ucl")
        and not game_has_started(p)
    ]
    plays.sort(key=lambda x: -x.get("edge", 0))

    strong_edges = [p for p in plays if p.get("edge", 0) >= 0.10]

    if not strong_edges:
        logger.info("No global high-confidence outliers found")
        return

    top = strong_edges[0]

    if top.get("prop_label") in ("HITS", "TOTAL_BASES", "HOME_RUNS"):
        text = generate_potd_from_play(top)
    else:
        text = generate_gotd_from_play(top)

    caption = "EDGE EQUATION GLOBAL — HIGH CONFIDENCE OUTLIER\n\n" + text
    logger.info(caption)
