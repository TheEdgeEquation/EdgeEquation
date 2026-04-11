import tweepy
import os
import sys

api_key = os.environ.get("X_API_KEY", "")
api_secret = os.environ.get("X_API_SECRET", "")
access_token = os.environ.get("X_ACCESS_TOKEN", "")
access_secret = os.environ.get("X_ACCESS_SECRET", "")

print("=== KEY DIAGNOSTICS ===")
print(f"API_KEY length: {len(api_key)}, starts: {api_key[:3]}..., ends: ...{api_key[-3:]}")
print(f"API_SECRET length: {len(api_secret)}, starts: {api_secret[:3]}..., ends: ...{api_secret[-3:]}")
print(f"ACCESS_TOKEN length: {len(access_token)}, starts: {access_token[:3]}..., ends: ...{access_token[-3:]}")
print(f"ACCESS_SECRET length: {len(access_secret)}, starts: {access_secret[:3]}..., ends: ...{access_secret[-3:]}")
print("=======================")

api_key = api_key.strip()
api_secret = api_secret.strip()
access_token = access_token.strip()
access_secret = access_secret.strip()

try:
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret
    )
    response = client.create_tweet(text="The algorithm doesn't guess. It calculates. #EdgeEquation")
    print(f"Tweet posted! ID: {response.data['id']}")
    print("Authentication successful!")
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)
