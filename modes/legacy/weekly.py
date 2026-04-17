import logging
from engine.stats_tracker import build_weekly_stats
from engine.content_generators import caption_weekly
from engine.social import post_tweet

logger = logging.getLogger(__name__)

def run_weekly():
    logger.info("MODE: weekly")

    stats = build_weekly_stats(style="ee")
    if stats["total"] == 0:
        logger.warning("No data for weekly roundup")
        return

    caption = caption_weekly(stats)
    post_tweet(caption)

    logger.info("Weekly summary posted")
