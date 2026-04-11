import tweepy
import os
import sys

try:
    client = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"]
    )
    response = client.create_tweet(text="The algorithm doesn't guess. It calculates. Connection test successful. #EdgeEquation")
    print(f"Tweet posted! ID: {response.data['id']}")
    print("Authentication successful!")
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

