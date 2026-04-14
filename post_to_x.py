import os
import logging
import tweepy
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
X_API_KEY = os.getenv("X_API_KEY", "")
X_API_SECRET = os.getenv("X_API_SECRET", "")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN", "")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET", "")
 
CBC_X_API_KEY = os.getenv("CBC_X_API_KEY", X_API_KEY)
CBC_X_API_SECRET = os.getenv("CBC_X_API_SECRET", X_API_SECRET)
CBC_X_ACCESS_TOKEN = os.getenv("CBC_X_ACCESS_TOKEN", X_ACCESS_TOKEN)
CBC_X_ACCESS_SECRET = os.getenv("CBC_X_ACCESS_SECRET", X_ACCESS_SECRET)
 
 
def _get_client(account="ee"):
    if account == "cbc":
        return tweepy.Client(
            consumer_key=CBC_X_API_KEY,
            consumer_secret=CBC_X_API_SECRET,
            access_token=CBC_X_ACCESS_TOKEN,
            access_token_secret=CBC_X_ACCESS_SECRET,
        )
    return tweepy.Client(
        consumer_key=X_API_KEY,
        consumer_secret=X_API_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_SECRET,
    )
 
 
def post_tweet(text, image_path=None, account="ee"):
    try:
        client = _get_client(account)
        text = text[:280]
        response = client.create_tweet(text=text)
        tweet_id = response.data["id"]
        logger.info("[" + account.upper() + "] Tweet posted: " + str(tweet_id))
        return tweet_id
    except Exception as e:
        logger.error("[" + account.upper() + "] Tweet failed: " + str(e))
        return None
 
 
def post_thread(tweets, account="ee"):
    try:
        client = _get_client(account)
        reply_to = None
        tweet_ids = []
        for text in tweets:
            text = text[:280]
            if reply_to:
                response = client.create_tweet(text=text, in_reply_to_tweet_id=reply_to)
            else:
                response = client.create_tweet(text=text)
            reply_to = response.data["id"]
            tweet_ids.append(reply_to)
        logger.info("[" + account.upper() + "] Thread posted: " + str(len(tweet_ids)) + " tweets")
        return tweet_ids
    except Exception as e:
        logger.error("[" + account.upper() + "] Thread failed: " + str(e))
        return []
 
 
def caption_announce():
    date_str = datetime.now().strftime("%A, %B %d")
    return ("EE scanning today:\n\nMLB * NBA * NHL\n\nPitcher Ks * NRFI/YRFI * Game totals\n\nProjections drop at 11 AM CDT.\n\nLive data. No feelings. Just facts.\n\n#EdgeEquation")[:280]
 
 
def caption_cbc_announce():
    return ("CASH BEFORE COFFEE — overnight slate incoming.\n\nKBO * NPB * EPL * Champions League\n\nProjections dropping shortly.\n\nThe algorithm never sleeps.\n\n#CashBeforeCoffee")[:280]
 
 
def caption_mlb_projections(projections):
    if not projections:
        return ""
    from engine.content_generator import generate_mlb_projection_post
    return generate_mlb_projection_post(projections)[:280]
 
 
def caption_pitcher_projections(projections):
    if not projections:
        return ""
    from engine.content_generator import generate_pitcher_projection_post
    return generate_pitcher_projection_post(projections)[:280]
 
 
def caption_nba_projections(projections):
    if not projections:
        return ""
    from engine.content_generator import generate_nba_projection_post
    return generate_nba_projection_post(projections)[:280]
 
 
def caption_nhl_projections(projections):
    if not projections:
        return ""
    from engine.content_generator import generate_nhl_projection_post
    return generate_nhl_projection_post(projections)[:280]
 
 
def caption_nrfi_probabilities(nrfi_plays):
    if not nrfi_plays:
        return ""
    from engine.content_generator import generate_nrfi_probability_post
    return generate_nrfi_probability_post(nrfi_plays)[:280]
 
 
def caption_results_ee(results):
    if not results:
        return "Results pending.\n\n#EdgeEquation #Results"
    from engine.content_generator import generate_results_post
    return generate_results_post(results)[:280]
 
 
def caption_weekly(stats):
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    win_rate = stats.get("win_rate", 0)
    net = stats.get("net_units", 0)
    prefix = "+" if net >= 0 else ""
    from engine.content_generator import get_daily_cta
    return ("WEEK IN REVIEW\n\n" + str(wins) + "-" + str(losses) + " (" + str(win_rate) + "%)\n" + prefix + str(net) + "u\n\nEvery result posted. Win or lose.\n\n" + get_daily_cta() + "\n\n#EdgeEquation #Results")[:280]
 
 
def caption_no_play():
    from engine.content_generator import generate_no_play_post
    return generate_no_play_post()[:280]
 
 
def caption_cbc_results(results):
    from engine.cbc_projector import format_cbc_results_post
    return format_cbc_results_post(results)[:280]
 
 
def caption_nba_playoffs(projections):
    from engine.playoff_projector import format_nba_playoff_post
    return format_nba_playoff_post(projections)[:280]
 
 
def caption_nhl_playoffs(projections):
    from engine.playoff_projector import format_nhl_playoff_post
    return format_nhl_playoff_post(projections)[:280]
