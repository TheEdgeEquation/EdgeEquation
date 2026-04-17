# core/x_client.py

import os
import tweepy

def get_x_client():
    """
    Returns an authenticated Tweepy client.
    Centralized so all posting uses the same interface.
    """
    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_secret = os.getenv("X_ACCESS_SECRET")

    if not all([api_key, api_secret, access_token, access_secret]):
        raise RuntimeError("Missing X API credentials.")

    auth = tweepy.OAuth1UserHandler(
        api_key,
        api_secret,
        access_token,
        access_secret
    )

    return tweepy.API(auth)
