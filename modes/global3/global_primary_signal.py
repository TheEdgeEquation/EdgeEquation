import logging
from engine.utils import game_has_started
from engine.content_generators import generate_gotd_from_play
from engine.edge_calculator import grade_all_props, calculate_nrfi_plays
from engine.prizepicks_scraper import fetch_prizepicks_props

logger = logging.getLogger(__name__)

def run_global_primary_signal():
    logger.info("MODE: global_primary_signal")

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

    game_plays = [
        p for p in plays
        if p.get("prop_label") not in ("K", "NRFI", "YRFI", "3PM", "PTS", "SOG", "AST", "REB")
    ]

    if not game_plays:
        logger.info("No global game-level edges for Primary Signal")
        return

    text = generate_gotd_from_play(game_plays[0])

    caption = "EDGE EQUATION GLOBAL — PRIMARY SIGNAL\n\n" + text
    logger.info(caption)
