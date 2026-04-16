import logging

logger = logging.getLogger(__name__)

try:
    # Correct location: root-level post_to_x.py
    from post_to_x import send_tweet as _send_tweet
except Exception:
    _send_tweet = None


def post_tweet(text):
    if not text:
        logger.error("post_tweet() called with empty text")
        return

    if _send_tweet:
        try:
            _send_tweet(text)
            logger.info("Tweet posted successfully")
        except Exception as e:
            logger.error("Tweet failed: " + str(e))
    else:
        logger.error("Underlying tweet sender missing — cannot post")
        logger.info("[DRY RUN] Would have posted:\n" + text)
