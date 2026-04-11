import tweepy
import os
import sys

def post_tweet(text, image_path=None):
    client = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"]
    )

    if image_path:
        auth = tweepy.OAuth1UserHandler(
            os.environ["X_API_KEY"],
            os.environ["X_API_SECRET"],
            os.environ["X_ACCESS_TOKEN"],
            os.environ["X_ACCESS_SECRET"]
        )
        api = tweepy.API(auth)
        media = api.media_upload(image_path)
        response = client.create_tweet(
            text=text,
            media_ids=[media.media_id]
        )
    else:
        response = client.create_tweet(text=text)

    print(f"Tweet posted! ID: {response.data['id']}")
    return response

if __name__ == "__main__":
    tweet_text = sys.argv[1] if len(sys.argv) > 1 else "Test post from The Edge Equation"
    img = sys.argv[2] if len(sys.argv) > 2 else None
    post_tweet(tweet_text, img)
