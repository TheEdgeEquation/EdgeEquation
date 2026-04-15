import argparse
import logging
import sys
import time
from datetime import datetime
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")
 
from engine.edge_calculator import grade_all_props, calculate_nrfi_plays
from engine.data_tracker import save_plays, build_weekly_stats, build_all_time_stats, save_results
from engine.score_checker import check_all_results
from engine.email_sender import send_projections_only_email, send_results_email
from engine.parlay_engine import build_game_parlay, build_prizepicks_parlay
from engine.personal_engine import build_personal_parlay, build_personal_prizepicks
from engine.kelly_calculator import apply_kelly_to_plays, get_bankroll_summary
from engine.analysis_generator import generate_all_analysis
from engine.content_generator import (
    generate_mlb_projection_post, generate_pitcher_projection_post,
    generate_nba_projection_post, generate_nhl_projection_post,
    generate_nrfi_probability_post, generate_results_post,
    generate_no_play_post, generate_kbo_projection_post,
    generate_npb_projection_post, generate_epl_projection_post,
    generate_ucl_projection_post,
)
from engine.reminder_generator import generate_daily_todo
from engine.closing_line_tracker import track_clv_for_plays, generate_clv_post
from engine.game_projector import get_mlb_game_projections, get_nba_game_projections, get_nhl_game_projections, get_mlb_pitcher_projections
from engine.playoff_projector import get_nba_playoff_projections, get_nhl_playoff_projections, format_nba_playoff_post, format_nhl_playoff_post
from engine.kbo_scraper import get_kbo_projections
from engine.npb_scraper import get_npb_projections
from engine.cbc_projector import get_epl_projections, get_ucl_projections
from post_to_x import post_tweet, caption_announce, caption_results_ee, caption_weekly
 
 
def _today():
    return datetime.now().strftime("%Y%m%d")
 
 
def _fetch_props():
    from engine.prop_generator import generate_all_props
    for attempt in range(1, 5):
        logger.info("Fetch attempt " + str(attempt) + " of 4")
        try:
            props = generate_all_props() or []
            if props:
                return props
        except Exception as e:
            logger.error("Props failed: " + str(e))
        if attempt < 4:
            time.sleep(5 * 60)
    return []
 
 
def run_announce(dry_run, no_graphic):
    logger.info("MODE: announce")
    caption = caption_announce()
    if not dry_run:
        post_tweet(caption)
        logger.info("Announce posted")
    else:
        logger.info("[DRY RUN] Announce:\n" + caption)
 
 
def run_daily(dry_run, no_graphic):
    logger.info("MODE: daily")
 
    logger.info("Fetching projections...")
    mlb_games = get_mlb_game_projections()
    mlb_pitchers = get_mlb_pitcher_projections()
    nba_games = get_nba_game_projections()
    nhl_games = get_nhl_game_projections()
    nrfi_plays = calculate_nrfi_plays() or []
 
    logger.info("Fetching overseas projections...")
    kbo_games = get_kbo_projections()
    npb_games = get_npb_projections()
    epl_games = get_epl_projections()
    ucl_games = get_ucl_projections()
 
    logger.info("MLB=" + str(len(mlb_games)) + " NBA=" + str(len(nba_games)) +
                " NHL=" + str(len(nhl_games)) + " KBO=" + str(len(kbo_games)) +
                " NPB=" + str(len(npb_games)) + " EPL=" + str(len(epl_games)))
 
    props = _fetch_props()
    graded_props = grade_all_props(props) if props else []
    all_plays = graded_props + nrfi_plays
    if all_plays:
        all_plays = apply_kelly_to_plays(all_plays)
        save_plays(all_plays, "ee")
        all_plays = track_clv_for_plays(all_plays)
 
    clv_plays = [p for p in all_plays if p.get("clv", 0) > 0.01]
    clv_post = generate_clv_post(clv_plays) if clv_plays else None
    analyses, why_passed = generate_all_analysis(all_plays)
    game_parlay = build_game_parlay()
    pp_parlay = build_prizepicks_parlay(all_plays)
 
    try:
        from engine.parlay_engine import evaluate_game_for_parlay, get_todays_games
        game_bets = []
        for game in get_todays_games():
            game_bets.extend(evaluate_game_for_parlay(game))
        personal_parlay = build_personal_parlay(game_bets)
    except Exception as e:
        logger.error("Personal parlay failed: " + str(e))
        personal_parlay = None
 
    personal_pp = build_personal_prizepicks(all_plays)
    bankroll = get_bankroll_summary()
    all_time = build_all_time_stats(style="ee")
 
    if not dry_run:
        if mlb_games:
            post_tweet(generate_mlb_projection_post(mlb_games))
            logger.info("MLB projections posted")
        if mlb_pitchers:
            post_tweet(generate_pitcher_projection_post(mlb_pitchers))
            logger.info("Pitcher projections posted")
        if nba_games:
            post_tweet(generate_nba_projection_post(nba_games))
            logger.info("NBA projections posted")
        if nhl_games:
            post_tweet(generate_nhl_projection_post(nhl_games))
            logger.info("NHL projections posted")
        if nrfi_plays:
            post_tweet(generate_nrfi_probability_post(nrfi_plays))
            logger.info("NRFI posted")
        if kbo_games:
            post_tweet(generate_kbo_projection_post(kbo_games))
            logger.info("KBO projections posted")
        if npb_games:
            post_tweet(generate_npb_projection_post(npb_games))
            logger.info("NPB projections posted")
        if epl_games:
            post_tweet(generate_epl_projection_post(epl_games))
            logger.info("EPL projections posted")
        if ucl_games:
            post_tweet(generate_ucl_projection_post(ucl_games))
            logger.info("UCL projections posted")
        if clv_post:
            post_tweet(clv_post)
        send_projections_only_email(
            mlb_games=mlb_games, mlb_pitchers=mlb_pitchers,
            nba_games=nba_games, nhl_games=nhl_games,
            nrfi_plays=nrfi_plays,
            personal_parlay=personal_parlay, personal_pp=personal_pp,
            bankroll_summary=bankroll, all_time_stats=all_time,
        )
        logger.info("Email sent")
    else:
        posts = sum([bool(mlb_games), bool(mlb_pitchers), bool(nba_games),
                     bool(nhl_games), bool(nrfi_plays), bool(kbo_games),
                     bool(npb_games), bool(epl_games), bool(ucl_games)])
        logger.info("[DRY RUN] Would post " + str(posts) + " projection posts to X")
        if mlb_games:
            logger.info("[DRY RUN] MLB sample:\n" + generate_mlb_projection_post(mlb_games[:2]))
        if kbo_games:
            logger.info("[DRY RUN] KBO sample:\n" + generate_kbo_projection_post(kbo_games[:2]))
 
 
def run_results(dry_run, no_graphic):
    logger.info("MODE: results")
    try:
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
            post_tweet(results_text)
            send_results_email(verified)
            logger.info("Results posted and emailed")
        else:
            logger.info("[DRY RUN] Results:\n" + results_text)
    except Exception as e:
        logger.error("Results failed: " + str(e))
 
 
def run_weekly(dry_run, no_graphic):
    logger.info("MODE: weekly")
    stats = build_weekly_stats(style="ee")
    if stats["total"] == 0:
        logger.warning("No data for weekly roundup")
        return
    caption = caption_weekly(stats)
    if not dry_run:
        post_tweet(caption)
        logger.info("Weekly roundup posted")
    else:
        logger.info("[DRY RUN] Weekly:\n" + caption)
 
 
def run_playoffs(dry_run, no_graphic):
    logger.info("MODE: playoffs")
    nba = get_nba_playoff_projections()
    nhl = get_nhl_playoff_projections()
    nba_post = format_nba_playoff_post(nba)
    nhl_post = format_nhl_playoff_post(nhl)
    if not dry_run:
        if nba_post:
            post_tweet(nba_post)
        if nhl_post:
            post_tweet(nhl_post)
    else:
        logger.info("[DRY RUN] NBA:\n" + nba_post)
        logger.info("[DRY RUN] NHL:\n" + nhl_post)
 
 
def run_weekly_reminder(dry_run, no_graphic):
    from engine.phase_reminder import run_phase_reminder
    run_phase_reminder("weekly")
 
 
def run_monthly_reminder(dry_run, no_graphic):
    from engine.phase_reminder import run_phase_reminder
    run_phase_reminder("monthly")
 
 
def run_phase2(dry_run, no_graphic):
    from engine.phase_reminder import run_phase_reminder
    run_phase_reminder("phase2")
 
 
def run_phase3(dry_run, no_graphic):
    from engine.phase_reminder import run_phase_reminder
    run_phase_reminder("phase3")
 
 
def run_phase4(dry_run, no_graphic):
    from engine.phase_reminder import run_phase_reminder
    run_phase_reminder("phase4")
 
 
MODES = {
    "announce": run_announce,
    "daily": run_daily,
    "results": run_results,
    "weekly": run_weekly,
    "playoffs": run_playoffs,
    "weekly_reminder": run_weekly_reminder,
    "monthly_reminder": run_monthly_reminder,
    "phase2": run_phase2,
    "phase3": run_phase3,
    "phase4": run_phase4,
}
 
 
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=list(MODES.keys()))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-graphic", action="store_true")
    args = parser.parse_args()
    logger.info("Starting | mode=" + args.mode + " | dry_run=" + str(args.dry_run))
    MODES[args.mode](dry_run=args.dry_run, no_graphic=args.no_graphic)
    logger.info("Run complete.")
 
 
if __name__ == "__main__":
    main()
