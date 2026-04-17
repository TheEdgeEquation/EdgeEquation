import logging
from engine.stats_tracker import build_all_time_stats
from engine.social import post_tweet

logger = logging.getLogger(__name__)

def run_monthly():
    logger.info("MODE: monthly")

    stats = build_all_time_stats(style="ee")
    caption = (
        "EDGE EQUATION — Monthly Summary\n\n"
        f"Total graded outputs: {stats.get('total', 0)}"
    )

    post_tweet(caption)
    logger.info("Monthly summary posted")
