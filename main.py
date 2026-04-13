import argparse
import logging
import sys
from datetime import datetime
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("main")
from engine.odds_fetcher import fetch_all_props
from engine.edge_calculator import grade_all_props, calculate_nrfi_plays
from engine.data_tracker import save_plays, load_plays, save_results, load_results, build_weekly_stats
from engine.visualizer import generate_main_graphic, generate_announce_graphic, generate_results_graphic, generate_weekly_graphic, generate_cbc_tease_graphic
from engine.score_checker import check_all_results
from engine.sms_sender import send_picks_sms, format_picks_for_sms
from post_to_x import post_tweet, caption_announce, caption_daily_ee, caption_results_ee, caption_cbc_tease, caption_cbc_drop, caption_cbc_results, caption_weekly
def _today():
    return datetime.now().strftime("%Y%m%d")
def _fetch_and_grade(style="ee"):
    logger.info("Fetching props from Odds API...")
    props = fetch_all_props()
    logger.info("Fetching NRFI/YRFI plays from MLB API...")
    nrfi_plays = calculate_nrfi_plays(style=style)
    all_props = (props or []) + (nrfi_plays or [])
    if not all_props:
        logger.warning("No props returned from any source")
        return []
    logger.info("Running Monte Carlo on " + str(len(props)) + " props...")
    graded_props = grade_all_props(props)
    all_plays = graded_props + nrfi_plays
    if not all_plays:
        logger.warning("No plays met threshold")
        return []
    save_plays(all_plays, style)
    logger.info(str(len(all_plays)) + " total plays saved (" + str(len(graded_props)) + " props + " + str(len(nrfi_plays)) + " NRFI/YRFI)")
    return all_plays
def _build_announce_games():
    raw = fetch_all_props()
    seen = set()
    games = []
    for p in raw:
        key = (p["sport_label"], p["team"], p["opponent"])
        if key not in seen:
            seen.add(key)
            try:
                dt = datetime.fromisoformat(p.get("commence_time", "").replace("Z", "+00:00"))
                time_str = dt.strftime("%I:%M %p")
            except Exception:
                time_str = "TBD"
            games.append({"sport_label": p["sport_label"], "home": p["team"], "away": p["opponent"], "time": time_str})
    return games[:12]
def run_announce(dry_run, no_graphic):
    logger.info("MODE: announce")
    games = _build_announce_games()
    sports = list({g["sport_label"] for g in games})
    date_str = datetime.now().strftime("%A, %B %d")
    sport_str = "  |  ".join(sports) if sports else "MLB  |  NHL  |  NBA"
    caption = ("📋 " + date_str + " — Games we are scanning today.\n\nMarkets: " + sport_str + "\nProps: Pitcher Ks  •  NRFI/YRFI  •  Player 3s  •  SOG\n\nA+/A/A- plays drop at 10:30 AM CDT.\n\nLive data. 100% Verified. No feelings. Just facts.\n\n#EdgeEquation #SportsBetting #PlayerProps #NRFI")
    if not dry_run:
        result = post_tweet(caption, None)
        logger.info("Post result: " + str(result))
    else:
        logger.info("[DRY RUN] Would post announce")
def run_daily(dry_run, no_graphic):
    logger.info("MODE: daily")
    plays = _fetch_and_grade(style="ee")
    if not plays:
        caption = "No A+/A/A- plays today.\n\nThe model runs 10,000 sims per line. No edge = no play.\n\nLive data. 100% Verified. No feelings. Just facts.\n\n#EdgeEquation #NoPlay"
        if not dry_run:
            post_tweet(caption, None)
        return
    logger.info("Sending picks via SMS...")
    sms_result = send_picks_sms(plays)
    logger.info("SMS result: " + str(sms_result))
    if dry_run:
        logger.info("[DRY RUN] SMS preview:\n" + format_picks_for_sms(plays))
def run_post(dry_run, no_graphic):
    logger.info("MODE: post")
    plays = load_plays(_today(), style="ee")
    if not plays:
        logger.warning("No plays found for today")
        return
    graphic = None
    if not no_graphic:
        try:
            graphic = generate_main_graphic(plays, style="ee")
        except Exception as e:
            logger.error("Graphic failed: " + str(e))
    caption = caption_daily_ee(plays)
    if not dry_run:
        result = post_tweet(caption, graphic)
        logger.info("Post result: " + str(result))
    else:
        logger.info("[DRY RUN] Would post daily plays")
def run_results(dry_run, no_graphic):
    logger.info("MODE: results")
    results = check_all_results(style="ee", date_str=_today())
    if not results:
        logger.warning("No results found today")
        caption = "Results pending — scores still coming in.\n\n#EdgeEquation #Results"
        if not dry_run:
            post_tweet(caption, None)
        return
    verified = [r for r in results if r.get("result_checked")]
    if not verified:
        logger.warning("No plays verified yet")
        caption = "Results pending — games still in progress.\n\n#EdgeEquation #Results"
        if not dry_run:
            post_tweet(caption, None)
        return
    graphic = None
    if not no_graphic:
        try:
            graphic = generate_results_graphic(results, style="ee")
        except Exception as e:
            logger.error("Graphic failed: " + str(e))
    caption = caption_results_ee(results)
    if not dry_run:
        result = post_tweet(caption, graphic)
        logger.info("Post result: " + str(result))
    else:
        logger.info("[DRY RUN] Would post results")
def run_weekly(dry_run, no_graphic):
    logger.info("MODE: weekly")
    stats = build_weekly_stats(style="ee")
    if stats["total"] == 0:
        logger.warning("No data for weekly roundup")
        return
    graphic = None
    if not no_graphic:
        try:
            graphic = generate_weekly_graphic(stats)
        except Exception as e:
            logger.error("Graphic failed: " + str(e))
    caption = caption_weekly(stats)
    if not dry_run:
        result = post_tweet(caption, graphic)
        logger.info("Post result: " + str(result))
    else:
        logger.info("[DRY RUN] Would post weekly")
def run_cash_tease(dry_run, no_graphic):
    logger.info("MODE: cash_tease")
    caption = caption_cbc_tease()
    if not dry_run:
        result = post_tweet(caption, None)
        logger.info("Post result: " + str(result))
    else:
        logger.info("[DRY RUN] Would post CBC tease")
def run_cash_drop(dry_run, no_graphic):
    logger.info("MODE: cash_drop")
    plays = _fetch_and_grade(style="cbc")
    if not plays:
        caption = "The algo ran tonight — no edge found.\n\nWe don't force plays. Back tomorrow.\n\n#CashBeforeCoffee #NoPlay"
        if not dry_run:
            post_tweet(caption, None)
        return
    graphic = None
    if not no_graphic:
        try:
            graphic = generate_main_graphic(plays, style="cbc")
        except Exception as e:
            logger.error("Graphic failed: " + str(e))
    caption = caption_cbc_drop(plays)
    if not dry_run:
        result = post_tweet(caption, graphic)
        logger.info("Post result: " + str(result))
    else:
        logger.info("[DRY RUN] Would post CBC drop")
def run_cash_results(dry_run, no_graphic):
    logger.info("MODE: cash_results")
    from datetime import timedelta
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    results = check_all_results(style="cbc", date_str=yesterday)
    if not results:
        logger.warning("No CBC results yesterday")
        return
    graphic = None
    if not no_graphic:
        try:
            graphic = generate_results_graphic(results, style="cbc")
        except Exception as e:
            logger.error("Graphic failed: " + str(e))
    caption = caption_cbc_results(results)
    if not dry_run:
        result = post_tweet(caption, graphic)
        logger.info("Post result: " + str(result))
    else:
        logger.info("[DRY RUN] Would post CBC results")
MODES = {"announce": run_announce, "daily": run_daily, "post": run_post, "results": run_results, "weekly": run_weekly, "cash_tease": run_cash_tease, "cash_drop": run_cash_drop, "cash_results": run_cash_results}
def main():
    parser = argparse.ArgumentParser(description="EdgeEquation Runner")
    parser.add_argument("--mode", required=True, choices=list(MODES.keys()))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-graphic", action="store_true")
    args = parser.parse_args()
    logger.info("Starting | mode=" + args.mode + " | dry_run=" + str(args.dry_run))
    MODES[args.mode](dry_run=args.dry_run, no_graphic=args.no_graphic)
    logger.info("Run complete.")
if __name__ == "__main__":
    main()
