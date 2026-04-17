import logging
from engine.utils import game_has_started
from engine.content_generators import generate_first_inning_from_play
from engine.social import post_tweet
from engine.public_tagging import tag_public_pick
from engine.edge_calculator import calculate_nrfi_plays

logger = logging.getLogger(__name__)

def run_first_inning_potd():
    logger.info("MODE: first_inning_potd")

    nrfi_plays = calculate_nrfi_plays() or []
    nrfi_plays = [p for p in nrfi_plays if not game_has_started(p)]

    if not nrfi_plays:
        logger.info("No NRFI/YRFI plays available")
        return

    nrfi_plays.sort(key=lambda x: -x.get("edge", 0))
    top_nrfi = nrfi_plays[0]

    fi_text = generate_first_inning_from_play(top_nrfi)
    if not fi_text:
        logger.warning("First Inning POTD generation returned empty")
        return

    caption = "EDGE EQUATION — FIRST INNING POTD\n\n" + fi_text

    post_tweet(caption)
    tag_public_pick(top_nrfi, "FIRST_INNING_POTD")

    logger.info("First Inning POTD posted")
