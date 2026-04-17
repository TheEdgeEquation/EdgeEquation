import logging
from engine.utils import game_has_started
from engine.content_generators import generate_potd_from_play
from engine.edge_calculator import grade_all_props, calculate_nrfi_plays
from engine.prizepicks_scraper import fetch_prizepicks_props

logger = logging.getLogger(__name__)

def run_global_prop_efficiency_signal():
    logger.info("MODE: global_prop_efficiency_signal")

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

    prop_plays = [
        p for p in plays
        if p.get("prop_label") not in ("NRFI", "YRFI")
    ]

    if not prop_plays:
        logger.info("No global prop edges for Prop Efficiency Signal")
        return

    text = generate_potd_from_play(prop_plays[0])

    caption = "EDGE EQUATION GLOBAL — PROP EFFICIENCY SIGNAL\n\n" + text
    logger.info(caption)
