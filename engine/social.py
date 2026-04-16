import logging

logger = logging.getLogger(__name__)

# We wrap your existing posting engine.
# If your repo uses a different file name, tell me and I’ll adjust instantly.

try:
    from engine.post_to_x import send_tweet as _send_tweet
except Exception:
    _send_tweet = None


def post_tweet(text):
    """
    Unified posting wrapper for EE 3.0.
    main.py calls this function for all posts.
    """
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
