# core/x_client.py

import os
import tweepy

def get_x_client():
    """
    Returns a Tweepy v1.1 API client.
    This is REQUIRED for Essential-tier posting.
    """
    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

    auth = tweepy.OAuth1UserHandler(
        api_key,
        api_secret,
        access_token,
        access_secret
    )

    # v1.1 client (Essential-tier safe)
    return tweepy.API(auth)
