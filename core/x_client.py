# core/x_client.py

import os
import tweepy


# Load credentials from environment variables
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")


def get_x_client():
    """
    Returns a Tweepy v1.1 API client for posting text tweets.
    """
    if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET]):
        raise RuntimeError("Missing X API credentials in environment variables.")

    auth = tweepy.OAuth1UserHandler(
        API_KEY,
        API_SECRET,
        ACCESS_TOKEN,
        ACCESS_SECRET
    )

    return tweepy.API(auth)


def attempt_post(text: str):
    """
    Attempts to post a text tweet using the v1.1 API.
    Raises exceptions on failure.
    """
    client = get_x_client()
    client.update_status(status=text)
