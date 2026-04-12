"""
post_to_x.py
Posts graphics + captions to X using Tweepy v4.
Handles both Edge Equation (professional) and Cash Before Coffee (fun) tones.
"""
import tweepy
import logging
import os
from datetime import datetime
from config.settings import (
    X_API_KEY, X_API_SECRET,
    X_ACCESS_TOKEN, X_ACCESS_SECRET,
)

logger = logging.getLogger(__name__)


def _get_client() -> tweepy.Client:
    return tweepy.Client(
        consumer_key=X_API_KEY,
        consumer_secret=X_API_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_SECRET,
    )


def _get_v1_api() -> tweepy.API:
    auth = tweepy.OAuth1UserHandler(
        X_API_KEY, X_API_SECRET,
        X_ACCESS_TOKEN, X_ACCESS_SECRET
    )
    return tweepy.API(auth)


def upload_media(image_path: str) -> str | None:
    if not image_path or not os.path.exists(image_path):
        logger.error(f"Image not found: {image_path}")
        return None
    try:
        api = _get_v1_api()
        media = api.media_upload(image_path)
        logger.info(f"Media uploaded: {media.media_id_string}")
        return media.media_id_string
    except Exception as e:
        logger.error(f"Media upload failed: {e}")
        return None


def post_tweet(text: str, image_path: str | None = None) -> bool:
    logger.info(f"X_API_KEY set: {bool(X_API_KEY)}")
    logger.info(f"X_API_SECRET set: {bool(X_API_SECRET)}")
    logger.info(f"X_ACCESS_TOKEN set: {bool(X_ACCESS_TOKEN)}")
    logger.info(f"X_ACCESS_SECRET set: {bool(X_ACCESS_SECRET)}")
    if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET]):
        logger.error("X API credentials not set — cannot post")
        return False

    media_ids = None
    if image_path:
        media_id = upload_media(image_path)
        if media_id:
            media_ids = [media_id]

    try:
        client = _get_client()
        resp = client.create_tweet(text=text, media_ids=media_ids)
        logger.info(f"Tweet posted: {resp.data['id']}")
        return True
    except tweepy.TweepyException as e:
        logger.error(f"Tweet failed: {e}")
        return False


def caption_announce(games_today: list[dict]) -> str:
    date = datetime.now().strftime("%A, %B %d")
    sport_labels = list({g.get("sport_label", "") for g in games_today})
    sports_str = " · ".join(sport_labels)
    return (
        f"📋 {date} — Games we're scanning today.\n\n"
        f"Markets: {sports_str}\n"
        f"Props: Pitcher K's · Player 3's · SOG · Receptions\n\n"
        f"A+/A/A- plays drop at 10:30 AM CDT.\n\n"
        f"Live data. 100% Verified. No feelings. Just facts.\n\n"
        f"#EdgeEquation #SportsBetting #PlayerProps"
    )


def caption_daily_ee(plays: list[dict]) -> str:
    ap_plays = [p for p in plays if p["grade"] == "A+"]
    a_plays  = [p for p in plays if p["grade"] == "A"]
    am_plays = [p for p in plays if p["grade"] == "A-"]

    lines = ["THE EDGE EQUATION — Today's Plays\n"]
    if ap_plays:
        lines.append("A+ PRECISION PLAYS:")
        for p in ap_plays:
            lines.append(f"  {p['player']} — {p['display_line']} {p['prop_label']} {p['display_odds']} [{p['confidence_score']}]")
    if a_plays:
        lines.append("\nA SHARP PLAYS:")
        for p in a_plays:
            lines.append(f"  {p['player']} — {p['display_line']} {p['prop_label']} {p['display_odds']} [{p['confidence_score']}]")
    if am_plays:
        lines.append("\nA- SHARP PLAYS:")
        for p in am_plays:
            lines.append(f"  {p['player']} — {p['display_line']} {p['prop_label']} {p['display_odds']} [{p['confidence_score']}]")

    lines.append(f"\n10,000 Monte Carlo sims. Poisson distribution. No gut feel.")
    lines.append("Live data. 100% Verified. No feelings. Just facts.")
    lines.append("\n#EdgeEquation #PlayerProps #SportsBetting")
    return "\n".join(lines)


def caption_results_ee(results: list[dict]) -> str:
    hits = sum(1 for r in results if r.get("hit"))
    total = len(results)
    date = datetime.now().strftime("%B %d")

    lines = [f"RESULTS — {date}  {hits}/{total}\n"]
    for r in results:
        marker = "✓" if r.get("hit") else "✗"
        lines.append(f"{marker} {r['player']} {r['display_line']} {r['prop_label']}")

    if hits == total:
        lines.append("\nClean sheet. The equation doesn't miss.")
    elif hits > total // 2:
        lines.append("\nRecord stays positive. Process over picks.")
    else:
        lines.append("\nTough day. Results posted win or lose — that's the difference.")

    lines.append("\n#EdgeEquation #Results #Transparency")
    return "\n".join(lines)


def caption_cbc_tease() -> str:
    return (
        "☕ Cash Before Coffee drops at 10:30 PM tonight 🔥\n\n"
        "Best overnight parlay + PrizePicks-style slip incoming.\n"
        "The algo already ran. You just have to stay up.\n\n"
        "Powered by The Edge Equation — 10,000 sims per prop.\n\n"
        "#CashBeforeCoffee #NightOwl #PrizePicks #Parlay"
    )


def caption_cbc_drop(plays: list[dict]) -> str:
    if not plays:
        return "☕ Tonight's slip is still cooking. Check back shortly. 🔥"

    lines = ["☕ CASH BEFORE COFFEE — Night Owl Special 🔥\n"]
    lines.append("OVERNIGHT PARLAY:")
    for p in plays[:4]:
        lines.append(f"  {p['player']} {p['display_line']} {p['prop_label']} {p['display_odds']}")

    lines.append("\nPRIZEPICKS SLIP:")
    for p in plays[:6]:
        lines.append(f"  {p['player']} {p['display_line']} {p['prop_label']}")

    lines.append("\nWe ran 10,000 simulations so you didn't have to.")
    lines.append("Go to sleep. Cash Before Coffee. ☕")
    lines.append("\n#CashBeforeCoffee #NightOwl #PrizePicks #Parlay")
    return "\n".join(lines)


def caption_cbc_results(results: list[dict]) -> str:
    hits = sum(1 for r in results if r.get("hit"))
    total = len(results)

    if hits == total:
        opener = f"Last night's Cash Before Coffee hit {hits}/{total} 🔥☕ Who's reloading tonight?"
    elif hits > total // 2:
        opener = f"Last night's Cash Before Coffee went {hits}/{total} ☕ Solid. Drop back tonight at 10:30."
    else:
        opener = f"Last night went {hits}/{total} — tough beats happen. Algorithm resets tonight. ☕"

    lines = [opener, ""]
    for r in results:
        marker = "✓" if r.get("hit") else "✗"
        lines.append(f"{marker} {r['player']} {r['display_line']} {r['prop_label']}")

    lines.append("\n#CashBeforeCoffee #Results #NightOwl")
    return "\n".join(lines)


def caption_weekly(stats: dict) -> str:
    return (
        f"WEEKLY ROUNDUP — {stats.get('week_label', '')}\n\n"
        f"Record: {stats['hits']}-{stats['misses']}\n"
        f"Win Rate: {stats['win_rate']:.1f}%\n"
        f"Units: +{stats['units']:.1f}u\n\n"
        f"Best play: {stats.get('best_play', 'N/A')}\n\n"
        f"Tracking every result, every week. Win or lose.\n"
        f"Live data. 100% Verified. No feelings. Just facts.\n\n"
        f"#EdgeEquation #WeeklyResults #SportsBetting"
    )
