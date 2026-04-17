import logging
from datetime import datetime
from engine.social import post_tweet
from engine.utils import get_daily_cta

logger = logging.getLogger(__name__)

def run_system_status():
    logger.info("MODE: system_status")

    date_str = datetime.now().strftime("%B %-d")
    caption = "\n".join([
        f"EDGE EQUATION — {date_str}",
        "",
        "System online.",
        "Scanning today's slate:",
        "",
        "MLB  |  NBA  |  NHL",
        "KBO  |  NPB  |  EPL  |  UCL",
        "",
        "Projections drop at 11:30 AM CDT.",
        "",
        get_daily_cta(),
        "#EdgeEquation",
    ])

    post_tweet(caption)
    logger.info("System status posted")
