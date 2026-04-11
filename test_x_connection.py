import tweepy
import os
import sys

api_key = os.environ.get("X_API_KEY", "").strip()
api_secret = os.environ.get("X_API_SECRET", "").strip()
access_token = os.environ.get("X_ACCESS_TOKEN", "").strip()
access_secret = os.environ.get("X_ACCESS_SECRET", "").strip()

print("=== DIAGNOSTICS ===")
print(f"API_KEY length: {len(api_key)}")
print(f"API_SECRET length: {len(api_secret)}")
print(f"ACCESS_TOKEN length: {len(access_token)}")
print(f"ACCESS_SECRET length: {len(access_secret)}")
print(f"Token user ID: {access_token.split('-')[0] if '-' in access_token else 'NO DASH'}")
print(f"Tweepy version: {tweepy.__version__}")
print("===================")

client = tweepy.Client(
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_secret
)

print("\n--- TEST 1: Verify credentials ---")
try:
    me = client.get_me()
    if me.data:
        print(f"AUTH WORKS! Logged in as: @{me.data.username}")
    else:
        print("No data returned")
        sys.exit(1)
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Status: {e.response.status_code}")
        try:
            print(f"Body: {e.response.text}")
        except:
            pass
    if hasattr(e, 'api_errors'):
        print(f"API errors: {e.api_errors}")
    sys.exit(1)

print("\n--- TEST 2: Post tweet ---")
try:
    r = client.create_tweet(text="The algorithm doesn't guess. It calculates. #EdgeEquation")
    print(f"TWEET POSTED! ID: {r.data['id']}")
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
    if hasattr(e, 'response') and e.response is not None:
        try:
            print(f"Body: {e.response.text}")
        except:
            pass
    sys.exit(1)

