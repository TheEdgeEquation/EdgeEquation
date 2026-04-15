import os
import logging
import tweepy
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
X_API_KEY = os.getenv("X_API_KEY", "")
X_API_SECRET = os.getenv("X_API_SECRET", "")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN", "")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET", "")
 
 
def _get_client():
    return tweepy.Client(
        consumer_key=X_API_KEY,
        consumer_secret=X_API_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_SECRET,
    )
 
 
def post_tweet(text, image_path=None, account="ee"):
    try:
        client = _get_client()
        response = client.create_tweet(text=text[:280])
        tweet_id = response.data["id"]
        logger.info("Tweet posted: " + str(tweet_id))
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
                resp = client.create_tweet(text=text[:280], in_reply_to_tweet_id=reply_to)
            else:
                resp = client.create_tweet(text=text[:280])
            reply_to = resp.data["id"]
            ids.append(reply_to)
        logger.info("Thread posted: " + str(len(ids)) + " tweets")
        return ids
    except Exception as e:
        logger.error("Thread failed: " + str(e))
        return []
 
 
def caption_announce():
    date_str = datetime.now().strftime("%A, %B %-d")
    return ("EDGE EQUATION — " + date_str + "\n\nScanning today's slate:\n\nMLB  NBA  NHL\nKBO  NPB  EPL\n\nProjections dropping shortly.\n\nThis is data. Not advice.\n\n#EdgeEquation")[:280]
 
 
def caption_results_ee(results):
    if not results:
        return "Results pending.\n\n#EdgeEquation"
    from engine.content_generator import generate_results_post
    return generate_results_post(results)[:280]
 
 
def caption_weekly(stats):
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    win_rate = stats.get("win_rate", 0)
    net = stats.get("net_units", 0)
    prefix = "+" if net >= 0 else ""
    return ("EDGE EQUATION — WEEK IN REVIEW\n\n" + str(wins) + "-" + str(losses) + " (" + str(win_rate) + "%)\n" + prefix + str(net) + "u\n\nEvery result posted.\nThis is data. Not advice.\n\n#EdgeEquation")[:280]
 
 
def caption_no_play():
    from engine.content_generator import generate_no_play_post
    return generate_no_play_post()[:280]
