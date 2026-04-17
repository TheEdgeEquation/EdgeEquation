import logging
from engine.utils import game_has_started, get_daily_cta
from engine.content_generators import (
    generate_gotd_from_play,
    generate_potd_from_play,
    generate_first_inning_from_play,
)
from engine.social import post_tweet
from engine.edge_calculator import grade_all_props, calculate_nrfi_plays
from engine.prizepicks_scraper import fetch_prizepicks_props

logger = logging.getLogger(__name__)

def run_daily():
    logger.info("MODE: daily")

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
    prop_plays = [p for p in plays if p.get("prop_label") not in ("NRFI", "YRFI")]
    nrfi_plays = [p for p in plays if p.get("prop_label") in ("NRFI", "YRFI")]

    caption_lines = ["EDGE EQUATION — DAILY CARD", ""]

    if game_plays:
        caption_lines.append("GAME OF THE DAY")
        caption_lines.append(generate_gotd_from_play(game_plays[0]))
        caption_lines.append("")

    if prop_plays:
        caption_lines.append("PROP OF THE DAY")
        caption_lines.append(generate_potd_from_play(prop_plays[0]))
        caption_lines.append("")

    if nrfi_plays:
        caption_lines.append("FIRST INNING POTD")
        caption_lines.append(generate_first_inning_from_play(nrfi_plays[0]))
        caption_lines.append("")

    caption_lines.append(get_daily_cta())
    caption_lines.append("#EdgeEquation")

    caption = "\n".join(caption_lines)
    post_tweet(caption)

    logger.info("Daily card posted")
