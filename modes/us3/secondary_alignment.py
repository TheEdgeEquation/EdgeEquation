import logging
from engine.utils import game_has_started
from engine.content_generators import generate_gotd_from_play, generate_potd_from_play
from engine.edge_calculator import grade_all_props, calculate_nrfi_plays
from engine.prizepicks_scraper import fetch_prizepicks_props

logger = logging.getLogger(__name__)

def run_secondary_alignment():
    logger.info("MODE: secondary_alignment")

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
    prop_plays = [
        p for p in plays
        if p.get("prop_label") not in ("NRFI", "YRFI")
    ]

    aligned = []
    for g in game_plays:
        for p in prop_plays:
            if g.get("game_id") == p.get("game_id") and g.get("side") == p.get("side"):
                aligned.append((g, p))

    if not aligned:
        logger.info("No secondary alignment edges found")
        return

    top_game, top_prop = aligned[0]

    caption = "\n".join([
        "EDGE EQUATION 3.0 — SECONDARY ALIGNMENT",
        "",
        "GAME EDGE",
        generate_gotd_from_play(top_game),
        "",
        "PROP EDGE",
        generate_potd_from_play(top_prop),
    ])

    logger.info(caption)
