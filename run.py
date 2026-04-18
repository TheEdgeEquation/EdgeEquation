# run.py

import logging
import sys

from picks import load_today_picks, validate_picks
from graphics import render_daily_card
from x_client import post_to_x
from config import BRAND_NAME, TAGLINE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("edge_equation_run")

def main() -> int:
    try:
        picks = load_today_picks()
        validate_picks(picks)
        logger.info("Loaded and validated %d picks.", len(picks))

        image_path = render_daily_card(picks)
        logger.info("Rendered daily card at %s", image_path)

        status_text = f"{BRAND_NAME} — {TAGLINE}\n{len(picks)} edges on today’s slate."
        post_to_x(status_text=status_text, media_path=image_path)
        logger.info("Successfully posted daily card to X.")
        return 0

    except Exception as e:
        logger.exception("Run failed: %s", e)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
