import argparse
import logging
import sys
import time
from datetime import datetime
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("main")
from engine.odds_fetcher import fetch_all_props
from engine.edge_calculator import grade_all_props, calculate_nrfi_plays
from engine.data_tracker import save_plays, load_plays, save_results, build_weekly_stats, build_all_time_stats
from engine.score_checker import check_all_results
from engine.email_sender import send_daily_email, send_no_play_email, send_results_email
from engine.parlay_engine import build_game_parlay, build_prizepicks_parlay, format_game_parlay_sms, format_prizepicks_sms
from engine.personal_engine import build_personal_parlay, build_personal_prizepicks
from engine.kelly_calculator import apply_kelly_to_plays, get_bankroll_summary, calculate_parlay_units
from engine.analysis_generator import generate_all_analysis
from engine.content_generator import generate_no_play_post, generate_results_post
from engine.reminder_generator import generate_daily_todo
from engine.closing_line_tracker import track_clv_for_plays, generate_clv_post
from post_to_x import post_tweet, caption_announce, caption_daily_ee, caption_results_ee, caption_weekly
 
 
def _today():
    return datetime.now().strftime("%Y%m%d")
 
 
def _fetch_and_grade(style="ee"):
    MAX_ATTEMPTS = 6
    WAIT_MINUTES = 5
    nrfi_plays = calculate_nrfi_plays(style=style) or []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        logger.info("Fetch attempt " + str(attempt) + " of " + str(MAX_ATTEMPTS))
        props = fetch_all_props() or []
        if props:
            logger.info("Props found on attempt " + str(attempt) + ": " + str(len(props)))
            graded_props = grade_all_props(props) or []
            all_plays = graded_props + nrfi_plays
            if all_plays:
                all_plays = apply_kelly_to_plays(all_plays)
                save_plays(all_plays, style)
                logger.info(str(len(all_plays)) + " total plays saved (" + str(len(graded_props)) + " props + " + str(len(nrfi_plays)) + " NRFI/YRFI)")
                return all_plays
        if nrfi_plays and attempt == 1:
            logger.info("NRFI plays available: " + str(len(nrfi_plays)))
        if attempt < MAX_ATTEMPTS:
            logger.info("Waiting " + str(WAIT_MINUTES) + " minutes before retry...")
            time.sleep(WAIT_MINUTES * 60)
    if nrfi_plays:
        nrfi_plays = apply_kelly_to_plays(nrfi_plays)
        save_plays(nrfi_plays, style)
        logger.info("Returning " + str(len(nrfi_plays)) + " NRFI plays only")
        return nrfi_plays
    return []
 
 
def run_announce(dry_run, no_graphic):
    logger.info("MODE: announce")
    sports = "MLB  |  NBA  |  NHL"
    date_str = datetime.now().strftime("%A, %B %d")
    caption = ("📋 " + date_str + " — Games we are scanning today.\n\nMarkets: " + sports + "\nProps: Pitcher Ks  *  NRFI/YRFI  *  3PM  *  SOG\n\nA+/A/A- plays drop at 10:30 AM CDT.\n\nLive data. 100% Verified. No feelings. Just facts.\n\n#EdgeEquation #SportsBetting #PlayerProps #NRFI")
    if not dry_run:
        result = post_tweet(caption, None)
        logger.info("Announce posted: " + str(result))
    else:
        logger.info("[DRY RUN] Would post announce")
 
 
def run_daily(dry_run, no_graphic):
    logger.info("MODE: daily")
    plays = _fetch_and_grade(style="ee")
    if not plays:
        if not dry_run:
            no_play_text = generate_no_play_post()
            post_tweet(no_play_text, None)
            send_no_play_email()
        else:
            logger.info("[DRY RUN] No plays today")
        return
    logger.info("Tracking CLV...")
    plays = track_clv_for_plays(plays)
    clv_plays = [p for p in plays if p.get("clv", 0) > 0.01]
    clv_post = generate_clv_post(clv_plays) if clv_plays else None
    logger.info("Generating analysis...")
    analyses, why_passed = generate_all_analysis(plays)
    logger.info("Building game parlay...")
    game_parlay = build_game_parlay()
    logger.info("Building PrizePicks slip...")
    pp_parlay = build_prizepicks_parlay(plays)
    logger.info("Building personal parlay...")
    from engine.parlay_engine import evaluate_game_for_parlay, get_todays_games
    game_bets = []
    for game in get_todays_games():
        bets = evaluate_game_for_parlay(game)
        game_bets.extend(bets)
    personal_parlay = build_personal_parlay(game_bets)
    logger.info("Building personal PrizePicks slip...")
    personal_pp = build_personal_prizepicks(plays)
    logger.info("Getting bankroll summary...")
    bankroll = get_bankroll_summary()
    all_time = build_all_time_stats(style="ee")
    logger.info("Generating to-do list...")
    todo = generate_daily_todo(plays, game_parlay, pp_parlay, bool(clv_plays))
    if not dry_run:
        result = send_daily_email(plays, analyses, game_parlay, pp_parlay, personal_parlay, personal_pp, bankroll, all_time, todo, clv_post, why_passed if why_passed else None)
        logger.info("Daily email sent: " + str(result))
    else:
        logger.info("[DRY RUN] Daily email would be sent with " + str(len(plays)) + " plays")
        logger.info("Plays: " + str([p.get("player") + " " + p.get("display_line", "") + " " + p.get("prop_label", "") for p in plays]))
        if game_parlay:
            logger.info("Game parlay: " + str(game_parlay["leg_count"]) + " legs edge=" + str(game_parlay["edge"]))
        if pp_parlay:
            logger.info("PrizePicks: " + str(pp_parlay["leg_count"]) + " legs edge=" + str(pp_parlay["edge"]))
 
 
def run_results(dry_run, no_graphic):
    logger.info("MODE: results")
    results = check_all_results(style="ee", date_str=_today())
    if not results:
        logger.warning("No results found")
        return
    verified = [r for r in results if r.get("result_checked")]
    if not verified:
        logger.warning("No verified results yet")
        return
    save_results(verified, style="ee")
    results_text = generate_results_post(verified)
    if not dry_run:
        post_tweet(results_text, None)
        send_results_email(verified)
        logger.info("Results posted and emailed")
    else:
        logger.info("[DRY RUN] Results:\n" + results_text)
 
 
def run_weekly(dry_run, no_graphic):
    logger.info("MODE: weekly")
    stats = build_weekly_stats(style="ee")
    if stats["total"] == 0:
        logger.warning("No data for weekly roundup")
        return
    caption = caption_weekly(stats)
    if not dry_run:
        post_tweet(caption, None)
        logger.info("Weekly roundup posted")
    else:
        logger.info("[DRY RUN] Would post weekly roundup")
 
 
def run_weekly_reminder(dry_run, no_graphic):
    logger.info("MODE: weekly_reminder")
    from engine.phase_reminder import run_phase_reminder
    run_phase_reminder("weekly")
 
 
def run_monthly_reminder(dry_run, no_graphic):
    logger.info("MODE: monthly_reminder")
    from engine.phase_reminder import run_phase_reminder
    run_phase_reminder("monthly")
 
 
def run_phase2(dry_run, no_graphic):
    logger.info("MODE: phase2")
    from engine.phase_reminder import run_phase_reminder
    run_phase_reminder("phase2")
 
 
def run_phase3(dry_run, no_graphic):
    logger.info("MODE: phase3")
    from engine.phase_reminder import run_phase_reminder
    run_phase_reminder("phase3")
 
 
def run_phase4(dry_run, no_graphic):
    logger.info("MODE: phase4")
    from engine.phase_reminder import run_phase_reminder
    run_phase_reminder("phase4")
 
 
MODES = {
    "announce": run_announce,
    "daily": run_daily,
    "results": run_results,
    "weekly": run_weekly,
    "weekly_reminder": run_weekly_reminder,
    "monthly_reminder": run_monthly_reminder,
    "phase2": run_phase2,
    "phase3": run_phase3,
    "phase4": run_phase4,
}
 
 
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
