import tweepy
import os

try:
    client = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"]
    )
    me = client.get_me()
    print(f"Connected to: @{me.data.username}")
    print(f"Account ID: {me.data.id}")
    print("Authentication successful!")
except Exception as e:
    print(f"Connection failed: {e}")
