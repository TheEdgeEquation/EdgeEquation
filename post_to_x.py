import os
import logging
import tweepy
from datetime import datetime

import time
import requests

def post_with_retry(post_func, text, max_retries=5):
    """
    Retry wrapper for posting to X.
    Retries only on transient 5xx errors.
    Deterministic, exponential backoff.
    """
    for attempt in range(1, max_retries + 1):
        try:
            return post_func(text)

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code

            # Retry only on transient server errors
            if status in (500, 502, 503, 504):
                wait = 2 ** attempt  # exponential backoff
                print(f"[POSTING] Transient {status} error. Retry {attempt}/{max_retries} in {wait}s")
                time.sleep(wait)
                continue

            # Non‑retryable error → fail immediately
            print(f"[POSTING] Non‑retryable error {status}: {e}")
            raise

        except Exception as e:
            # Network glitch or unknown transient failure
            wait = 2 ** attempt
            print(f"[POSTING] Unexpected error on attempt {attempt}: {e}. Retrying in {wait}s")
            time.sleep(wait)
            continue

    # If all retries fail:
    raise RuntimeError(f"[POSTING] Failed after {max_retries} retries.")

 
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
