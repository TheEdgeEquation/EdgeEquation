# x_client.py

import logging
from typing import Optional
import tweepy  # make sure tweepy is in your requirements

from config import (
    X_API_KEY,
    X_API_SECRET,
    X_ACCESS_TOKEN,
    X_ACCESS_TOKEN_SECRET,
    validate_x_env,
)

logger = logging.getLogger(__name__)

def get_x_client() -> tweepy.API:
    validate_x_env()
    auth = tweepy.OAuth1UserHandler(
        X_API_KEY,
        X_API_SECRET,
        X_ACCESS_TOKEN,
        X_ACCESS_TOKEN_SECRET,
    )
    api = tweepy.API(auth)
    api.verify_credentials()
    logger.info("X client verified.")
    return api

def post_to_x(status_text: str, media_path: Optional[str] = None) -> None:
    api = get_x_client()
    if media_path:
        media = api.media_upload(media_path)
        api.update_status(status=status_text, media_ids=[media.media_id])
    else:
        api.update_status(status=status_text)
    logger.info("Posted to X.")
