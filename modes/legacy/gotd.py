import logging
from engine.utils import game_has_started
from engine.content_generators import generate_gotd_from_play
from engine.social import post_tweet
from engine.public_tagging import tag_public_pick
from engine.edge_calculator import grade_all_props, calculate_nrfi_plays
from engine.prizepicks_scraper import fetch_prizepicks_props

logger = logging.getLogger(__name__)

def run_gotd():
    logger.info("MODE: gotd")

    props = fetch_prizepicks_props() or []
    graded = grade_all_props(props)
    nrfi = calculate_nrfi_plays() or []
    plays = graded + nrfi

    plays = [p for p in plays if not game_has_started(p)]
    plays.sort(key=lambda x: -x.get("edge", 0))

    game_plays = [
        p for p in plays
        if p.get("prop_label") not in ("K", "NRFI", "YRFI", "3PM", "PTS", "SOG", "AST", "REB")
    ]

    if not game_plays:
        logger.info("No game-level edges for GOTD")
        return

    top_game = game_plays[0]
    text = generate_gotd_from_play(top_game)

    caption = "EDGE EQUATION — GAME OF THE DAY\n\n" + text

    post_tweet(caption)
    tag_public_pick(top_game, "GOTD")

    logger.info("GOTD posted")
