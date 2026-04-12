"""
EngagementChecker — Monitors X engagement metrics for content gating
PrizePicks and Cash Before Coffee cards unlock when engagement threshold is met.
"""
import os
import tweepy
from datetime import datetime


class EngagementChecker:
    def __init__(self, client=None):
        if client is not None:
            self.client = client
        else:
            # Auto-init tweepy client from env vars (unified X_ prefix)
            self.client = tweepy.Client(
                bearer_token=os.environ.get("X_BEARER_TOKEN", ""),
                consumer_key=os.environ.get("X_API_KEY", ""),
                consumer_secret=os.environ.get("X_API_SECRET", ""),
                access_token=os.environ.get("X_ACCESS_TOKEN", ""),
                access_token_secret=os.environ.get("X_ACCESS_SECRET", ""),
            )

    def get_recent_engagement(self, hours=24):
        """Get engagement metrics for recent tweets."""
        try:
            me = self.client.get_me()
            if not me or not me.data:
                return {"total_engagement": 0, "tweets_checked": 0}
            user_id = me.data.id
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=10,
                tweet_fields=["public_metrics", "created_at"],
            )
            if not tweets or not tweets.data:
                return {"total_engagement": 0, "tweets_checked": 0}
            total = 0
            count = 0
            for tweet in tweets.data:
                metrics = tweet.public_metrics or {}
                total += metrics.get("like_count", 0)
                total += metrics.get("retweet_count", 0)
                total += metrics.get("reply_count", 0)
                total += metrics.get("impression_count", 0) // 100  # weight impressions lower
                count += 1
            return {"total_engagement": total, "tweets_checked": count}
        except Exception as e:
            print(f"  [!] Engagement check failed: {e}")
            return {"total_engagement": 0, "tweets_checked": 0, "error": str(e)}

    def check_milestones(self, threshold=50):
        """
        Check if engagement meets the threshold for content unlocks.
        Returns dict with unlock status.
        """
        metrics = self.get_recent_engagement()
        engagement = metrics.get("total_engagement", 0)
        unlocked = engagement >= threshold
        return {
            "engagement": engagement,
            "threshold": threshold,
            "unlocked": unlocked,
            "timestamp": datetime.now().isoformat(),
            "detail": metrics,
        }
