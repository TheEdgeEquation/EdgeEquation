import logging
from engine.utils import game_has_started
from engine.content_generators import generate_potd_from_play
from engine.social import post_tweet
from engine.public_tagging import tag_public_pick
from engine.edge_calculator import grade_all_props, calculate_nrfi_plays
from engine.prizepicks_scraper import fetch_prizepicks_props

logger = logging.getLogger(__name__)

def run_potd():
    logger.info("MODE: potd")

    props = fetch_prizepicks_props() or []
    graded = grade_all_props(props)
    nrfi = calculate_nrfi_plays() or []
    plays = graded + nrfi

    plays = [p for p in plays if not game_has_started(p)]
    plays.sort(key=lambda x: -x.get("edge", 0))

    prop_plays = [
        p for p in plays
        if p.get("prop_label") not in ("NRFI", "YRFI")
    ]

    if not prop_plays:
        logger.info("No prop edges for POTD")
        return

    top_prop = prop_plays[0]
    text = generate_potd_from_play(top_prop)

    caption = "EDGE EQUATION — PROP OF THE DAY\n\n" + text

    post_tweet(caption)
    tag_public_pick(top_prop, "POTD")

    logger.info("POTD posted")
