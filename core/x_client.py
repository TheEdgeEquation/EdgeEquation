# core/x_client.py
"""
X (Twitter) Client Wrapper for The Edge Equation.

- Uses v1.1 API (Essential-tier compatible)
- Centralizes auth and client creation
- Provides a single get_x_client() entrypoint
"""

import os
from typing import Optional

import tweepy


_client_cache: Optional[tweepy.API] = None


class XClientConfigError(Exception):
    """Raised when X client configuration is invalid or incomplete."""
    pass


def _load_credentials() -> dict:
    """
    Load X API credentials from environment variables.

    Required:
        X_API_KEY
        X_API_SECRET
        X_ACCESS_TOKEN
        X_ACCESS_TOKEN_SECRET
    """
    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

    missing = [
        name
        for name, value in [
            ("X_API_KEY", api_key),
            ("X_API_SECRET", api_secret),
            ("X_ACCESS_TOKEN", access_token),
            ("X_ACCESS_TOKEN_SECRET", access_token_secret),
        ]
        if not value
    ]

    if missing:
        raise XClientConfigError(
            f"Missing X credentials: {', '.join(missing)}. "
            "Set these environment variables before posting."
        )

    return {
        "api_key": api_key,
        "api_secret": api_secret,
        "access_token": access_token,
        "access_token_secret": access_token_secret,
    }


def _create_client() -> tweepy.API:
    """
    Create a tweepy API client using v1.1 endpoints.
    """
    creds = _load_credentials()

    auth = tweepy.OAuth1UserHandler(
        creds["api_key"],
        creds["api_secret"],
        creds["access_token"],
        creds["access_token_secret"],
    )

    api = tweepy.API(
        auth,
        wait_on_rate_limit=True,
        wait_on_rate_limit_notify=False,
    )

    # Optional: lightweight sanity check (can be commented out if you prefer)
    try:
        api.verify_credentials()
    except Exception as e:
        raise XClientConfigError(f"Failed to verify X credentials: {e}")

    return api


def get_x_client() -> tweepy.API:
    """
    Return a singleton X client instance.

    All posting should go through this function.
    """
    global _client_cache

    if _client_cache is not None:
        return _client_cache

    _client_cache = _create_client()
    return _client_cache
