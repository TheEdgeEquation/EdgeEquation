import os
import logging
import tweepy
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
X_API_KEY = os.getenv("X_API_KEY", "")
X_API_SECRET = os.getenv("X_API_SECRET", "")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN", "")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET", "")
 
logger.info("post_to_x: X_API_KEY set: " + str(bool(X_API_KEY)))
logger.info("post_to_x: X_API_SECRET set: " + str(bool(X_API_SECRET)))
logger.info("post_to_x: X_ACCESS_TOKEN set: " + str(bool(X_ACCESS_TOKEN)))
logger.info("post_to_x: X_ACCESS_SECRET set: " + str(bool(X_ACCESS_SECRET)))
 
 
def post_tweet(text, image_path=None):
    try:
        client = tweepy.Client(
            consumer_key=X_API_KEY,
            consumer_secret=X_API_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_SECRET,
        )
        if image_path and os.path.exists(image_path):
            auth = tweepy.OAuth1UserHandler(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET)
            api = tweepy.API(auth)
            media = api.media_upload(image_path)
            response = client.create_tweet(text=text[:280], media_ids=[media.media_id])
        else:
            response = client.create_tweet(text=text[:280])
        tweet_id = response.data["id"]
        logger.info("Tweet posted: " + str(tweet_id))
        return tweet_id
    except Exception as e:
        logger.error("Tweet failed: " + str(e))
        return None
 
 
def caption_announce(games=None):
    date_str = datetime.now().strftime("%A, %B %d")
    return ("EE scanning today:\n\nMLB * NBA * NHL\n\nPitcher Ks * NRFI/YRFI * 3PM * SOG\n\nA+/A/A- plays via email at 10:30 AM CDT.\n\nLive data. No feelings. Just facts.\n\n#EdgeEquation")[:280]
 
 
def caption_daily_ee(plays):
    if not plays:
        return "No edge found today. The model does not force plays.\n\nNo feelings. Just facts.\n\n#EdgeEquation #NoPlay"
    n = len(plays)
    grade_order = {"A+": 0, "A": 1, "A-": 2}
    sorted_plays = sorted(plays, key=lambda x: (grade_order.get(x.get("grade", "A-"), 9), -x.get("edge", 0)))
    top = sorted_plays[0]
    grade = top.get("grade", "A")
    player = top.get("player", "")
    dl = top.get("display_line", "")
    prop = top.get("prop_label", "")
    return (grade + " TIER — " + player + " " + dl + " " + prop + "\n\n" + str(n) + " plays today. Algorithm approved.\n\nFull breakdown in email.\n\nNo feelings. Just facts.\n\n#EdgeEquation #MLB")[:280]
 
 
def caption_results_ee(results):
    if not results:
        return "Results pending.\n\n#EdgeEquation #Results"
    verified = [r for r in results if r.get("result_checked")]
    wins = sum(1 for r in verified if r.get("won"))
    losses = len(verified) - wins
    date_str = datetime.now().strftime("%B %d")
    lines = [date_str + " RESULTS", ""]
    for r in verified[:4]:
        symbol = "WIN" if r.get("won") else "LOSS"
        player = r.get("player", "")
        dl = r.get("display_line", "")
        prop = r.get("prop_label", "")
        actual = r.get("actual_result", "")
        result_str = " (" + str(actual) + ")" if actual else ""
        lines.append(symbol + " " + player + " " + dl + " " + prop + result_str)
    lines += ["", str(wins) + "-" + str(losses) + " today", "", "No feelings. Just facts.", "#EdgeEquation #Results"]
    return "\n".join(lines)[:280]
 
 
def caption_weekly(stats):
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    win_rate = stats.get("win_rate", 0)
    net = stats.get("net_units", 0)
    prefix = "+" if net >= 0 else ""
    return ("WEEK IN REVIEW\n\n" + str(wins) + "-" + str(losses) + " (" + str(win_rate) + "%)\n" + prefix + str(net) + "u\n\nEvery result posted. Win or lose.\nNo feelings. Just facts.\n\n#EdgeEquation #Results")[:280]
 
 
def caption_cbc_tease():
    return "Cash Before Coffee is coming.\n\nOvernight analytics. Markets books ignore.\n\nThe algorithm does not sleep.\n\n#CashBeforeCoffee"[:280]
 
 
def caption_cbc_drop(plays):
    n = len(plays) if plays else 0
    return ("CASH BEFORE COFFEE\n\n" + str(n) + " plays tonight.\nAlgorithm approved.\n\nWhile you sleep the edge compounds.\n\n#CashBeforeCoffee")[:280]
 
 
def caption_cbc_results(results):
    verified = [r for r in results if r.get("result_checked")] if results else []
    wins = sum(1 for r in verified if r.get("won"))
    losses = len(verified) - wins
    return ("CASH BEFORE COFFEE — RESULTS\n\n" + str(wins) + "-" + str(losses) + " overnight\n\nThe algorithm ran while you slept.\n\n#CashBeforeCoffee #Results")[:280]
