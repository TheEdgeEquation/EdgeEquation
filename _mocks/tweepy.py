"""Mock tweepy for local validation testing (not available in sandbox)."""
class Client:
    def __init__(self, **kwargs): pass
    def create_tweet(self, **kwargs): return type('R', (), {'data': {'id': '000'}})()
    def get_me(self): return type('R', (), {'data': type('D', (), {'id': '1'})()})()
    def get_users_tweets(self, **kwargs): return type('R', (), {'data': None})()
    def search_recent_tweets(self, **kwargs): return type('R', (), {'data': None})()
    def like(self, tweet_id): pass

class OAuth1UserHandler:
    def __init__(self, *args): pass

class API:
    def __init__(self, auth): pass
    def media_upload(self, filename): return type('M', (), {'media_id': 123})()
