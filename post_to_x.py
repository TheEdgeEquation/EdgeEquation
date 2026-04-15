import os
import logging
import tweepy
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
X_API_KEY = os.getenv("X_API_KEY", "")
X_API_SECRET = os.getenv("X_API_SECRET", "")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN", "")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET", "")
 
MAX_CHARS = 25000  # X Premium limit
 
 
def _get_client():
    return tweepy.Client(
        consumer_key=X_API_KEY,
        consumer_secret=X_API_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_SECRET,
    )
 
 
def post_tweet(text, image_path=None, account="ee", long_form=False):
    try:
        client = _get_client()
        text = text[:MAX_CHARS]
        response = client.create_tweet(text=text)
        tweet_id = response.data["id"]
        logger.info("Tweet posted: " + str(tweet_id) + " (" + str(len(text)) + " chars)")
        return tweet_id
    except Exception as e:
        logger.error("Tweet failed: " + str(e))
        return None
 
 
def post_thread(tweets, account="ee"):
    try:
        client = _get_client()
        reply_to = None
        ids = []
        for text in tweets:
            if reply_to:
                resp = client.create_tweet(
                    text=text[:MAX_CHARS],
                    in_reply_to_tweet_id=reply_to
                )
            else:
                resp = client.create_tweet(text=text[:MAX_CHARS])
            reply_to = resp.data["id"]
            ids.append(reply_to)
        logger.info("Thread posted: " + str(len(ids)) + " tweets")
        return ids
    except Exception as e:
        logger.error("Thread failed: " + str(e))
        return []
 
 
def caption_announce():
    from engine.content_generator import generate_system_status_post
    return generate_system_status_post()
 
 
def caption_results_ee(results):
    from engine.content_generator import generate_results_post
    return generate_results_post(results)
 
 
def caption_weekly(stats):
    from engine.content_generator import generate_monday_accountability_thread
    return generate_monday_accountability_thread(stats)
 
 
def caption_no_play():
    from engine.content_generator import generate_no_play_post
    return generate_no_play_post()
