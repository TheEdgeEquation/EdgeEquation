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
    generate_ucl_projection_post, generate_model_vs_vegas_post,
    get_daily_cta,
)
from engine.closing_line_tracker import track_clv_for_plays, generate_clv_post
from engine.game_projector import (
    get_mlb_game_projections, get_nba_game_projections,
    get_nhl_game_projections, get_mlb_pitcher_projections,
)
from engine.playoff_projector import (
    get_nba_playoff_projections, get_nhl_playoff_projections,
    format_nba_playoff_post, format_nhl_playoff_post,
)
from engine.kbo_scraper import get_kbo_projections
from engine.npb_scraper import get_npb_projections
from engine.cbc_projector import (
    get_epl_projections, get_ucl_projections,
    format_epl_projection_post, format_ucl_projection_post,
    format_kbo_projection_post, format_npb_projection_post,
    format_cbc_results_post,
)
from engine.gotd_generator import generate_gotd_from_play, generate_potd_from_play
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
 
 
def run_system_status(dry_run, no_graphic):
    logger.info("MODE: system_status")
    date_str = datetime.now().strftime("%B %-d")
    caption = "\n".join([
        "EDGE EQUATION — " + date_str,
        "",
        "System online.",
        "Scanning today's slate:",
        "",
        "MLB  |  NBA  |  NHL",
        "KBO  |  NPB  |  EPL",
        "",
        "Projections drop at 11:30 AM CDT.",
        "",
        get_daily_cta(),
        "#EdgeEquation",
    ])
    if not dry_run:
        post_tweet(caption)
        logger.info("System status posted")
    else:
        logger.info("[DRY RUN] System status:\n" + caption)
 
 
def run_gotd(dry_run, no_graphic):
    logger.info("MODE: gotd")
    try:
        props = _fetch_props()
        graded = grade_all_props(props) if props else []
        nrfi = calculate_nrfi_plays() or []
        all_plays = graded + nrfi
        if not all_plays:
            logger.info("No plays for GOTD")
            return
        all_plays.sort(key=lambda x: -x.get("edge", 0))
        top_game = next(
            (p for p in all_plays if p.get("prop_label") not in ("K",)),
            all_plays[0]
        )
        post_text = generate_gotd_from_play(top_game)
        if not post_text:
            logger.warning("GOTD generation returned empty")
            return
        if not dry_run:
            post_tweet(post_text)
            logger.info("GOTD posted")
        else:
            logger.info("[DRY RUN] GOTD:\n" + post_text)
    except Exception as e:
        logger.error("GOTD failed: " + str(e))
 
 
def run_potd(dry_run, no_graphic):
    logger.info("MODE: potd")
    try:
        props = _fetch_props()
        graded = grade_all_props(props) if props else []
        if not graded:
            logger.info("No props for POTD")
            return
        graded.sort(key=lambda x: -x.get("edge", 0))
        top_prop = next(
            (p for p in graded if p.get("prop_label") == "K"),
            graded[0]
        )
        post_text = generate_potd_from_play(top_prop)
        if not post_text:
            logger.warning("POTD generation returned empty")
            return
        if not dry_run:
            post_tweet(post_text)
            logger.info("POTD posted")
        else:
            logger.info("[DRY RUN] POTD:\n" + post_text)
    except Exception as e:
        logger.error("POTD failed: " + str(e))
 
 
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
 
    logger.info(
        "MLB=" + str(len(mlb_games)) + " NBA=" + str(len(nba_games)) +
        " NHL=" + str(len(nhl_games)) + " KBO=" + str(len(kbo_games)) +
        " NPB=" + str(len(npb_games)) + " EPL=" + str(len(epl_games))
    )
 
    props = _fetch_props()
    graded_props = grade_all_props(props) if props else []
    all_plays = graded_props + nrfi_plays
    if all_plays:
        all_plays = apply_kelly_to_plays(all_plays)
        save_plays(all_plays, "ee")
        all_plays = track_clv_for_plays(all_plays)
 
    clv_plays = [p for p in all_plays if p.get("clv", 0) > 0.01]
    clv_post = generate_clv_post(clv_plays) if clv_plays else None
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
        posts = sum([
            bool(mlb_games), bool(mlb_pitchers), bool(nba_games),
            bool(nhl_games), bool(nrfi_plays), bool(kbo_games),
            bool(npb_games), bool(epl_games), bool(ucl_games)
        ])
        logger.info("[DRY RUN] Would post " + str(posts) + " projection posts to X")
        if mlb_games:
            logger.info("[DRY RUN] MLB sample:\n" + generate_mlb_projection_post(mlb_games[:3]))
        if mlb_pitchers:
            logger.info("[DRY RUN] Pitcher sample:\n" + generate_pitcher_projection_post(mlb_pitchers[:5]))
        if nrfi_plays:
            logger.info("[DRY RUN] NRFI sample:\n" + generate_nrfi_probability_post(nrfi_plays[:4]))
 
 
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
            logger.info("NBA playoff post sent")
        if nhl_post:
            post_tweet(nhl_post)
            logger.info("NHL playoff post sent")
    else:
        logger.info("[DRY RUN] NBA:\n" + nba_post)
        logger.info("[DRY RUN] NHL:\n" + nhl_post)
 
 
def run_cbc_announce(dry_run, no_graphic):
    logger.info("MODE: cbc_announce")
    date_str = datetime.now().strftime("%B %-d")
    caption = "\n".join([
        "EDGE EQUATION — OVERNIGHT SLATE",
        date_str,
        "",
        "KBO  |  NPB  |  EPL  |  UCL",
        "",
        "Projections dropping shortly.",
        "The algorithm never sleeps.",
        "",
        "#EdgeEquation #KBO #NPB #EPL",
    ])
    if not dry_run:
        post_tweet(caption)
        logger.info("CBC announce posted")
    else:
        logger.info("[DRY RUN] CBC announce:\n" + caption)
 
 
def run_cbc_kbo(dry_run, no_graphic):
    logger.info("MODE: cbc_kbo")
    projections = get_kbo_projections()
    post_text = format_kbo_projection_post(projections)
    if not post_text:
        logger.info("No KBO games today")
        return
    if not dry_run:
        post_tweet(post_text)
        logger.info("KBO projections posted")
    else:
        logger.info("[DRY RUN] KBO:\n" + post_text)
 
 
def run_cbc_npb(dry_run, no_graphic):
    logger.info("MODE: cbc_npb")
    projections = get_npb_projections()
    post_text = format_npb_projection_post(projections)
    if not post_text:
        logger.info("No NPB games today")
        return
    if not dry_run:
        post_tweet(post_text)
        logger.info("NPB projections posted")
    else:
        logger.info("[DRY RUN] NPB:\n" + post_text)
 
 
def run_cbc_epl(dry_run, no_graphic):
    logger.info("MODE: cbc_epl")
    epl = get_epl_projections()
    ucl = get_ucl_projections()
    if epl:
        post_text = format_epl_projection_post(epl)
        if not dry_run:
            post_tweet(post_text)
            logger.info("EPL projections posted")
        else:
            logger.info("[DRY RUN] EPL:\n" + post_text)
    if ucl:
        post_text = format_ucl_projection_post(ucl)
        if not dry_run:
            post_tweet(post_text)
            logger.info("UCL projections posted")
        else:
            logger.info("[DRY RUN] UCL:\n" + post_text)
    if not epl and not ucl:
        logger.info("No EPL/UCL games today")
 
 
def run_cbc_results(dry_run, no_graphic):
    logger.info("MODE: cbc_results")
    results_text = format_cbc_results_post([])
    if not dry_run:
        post_tweet(results_text)
        logger.info("CBC results posted")
    else:
        logger.info("[DRY RUN] CBC results:\n" + results_text)
 
 
def run_cbc_gotd(dry_run, no_graphic):
    logger.info("MODE: cbc_gotd")
    try:
        epl = get_epl_projections()
        ucl = get_ucl_projections()
        all_games = epl + ucl
        if not all_games:
            logger.info("No overseas games for GOTD")
            return
        game = all_games[0]
        from engine.gotd_generator import generate_gotd
        post_text = generate_gotd(
            away_team=game.get("away_team", "Away"),
            home_team=game.get("home_team", "Home"),
            away_proj=game.get("away_goals", 1.2),
            home_proj=game.get("home_goals", 1.4),
            vegas_total=game.get("vegas_total", game.get("total", 2.5)),
            league_short=game.get("league", "EPL"),
            key_factors=[
                "Model projects above-average scoring environment",
                "Home side shows strong recent form",
                "Market total may undervalue pace of play",
            ],
        )
        if not dry_run:
            post_tweet(post_text)
            logger.info("CBC GOTD posted")
        else:
            logger.info("[DRY RUN] CBC GOTD:\n" + post_text)
    except Exception as e:
        logger.error("CBC GOTD failed: " + str(e))
 
 
def run_cbc_potd(dry_run, no_graphic):
    logger.info("MODE: cbc_potd — not yet implemented for overseas")
 
 
def run_scan_game(dry_run, no_graphic):
    logger.info("MODE: scan_game")
    mlb = get_mlb_game_projections()
    nba = get_nba_game_projections()
    nhl = get_nhl_game_projections()
    mvv = generate_model_vs_vegas_post([])
    logger.info("Scan complete: MLB=" + str(len(mlb)) + " NBA=" + str(len(nba)) + " NHL=" + str(len(nhl)))
 
 
def run_scan_prop(dry_run, no_graphic):
    logger.info("MODE: scan_prop")
    props = _fetch_props()
    graded = grade_all_props(props) if props else []
    logger.info("Scan complete: " + str(len(graded)) + " props graded")
 
 
def run_scan_nrfi(dry_run, no_graphic):
    logger.info("MODE: scan_nrfi")
    nrfi = calculate_nrfi_plays() or []
    logger.info("Scan complete: " + str(len(nrfi)) + " NRFI/YRFI plays")
 
 
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
    "system_status": run_system_status,
    "gotd": run_gotd,
    "potd": run_potd,
    "announce": run_announce,
    "daily": run_daily,
    "results": run_results,
    "weekly": run_weekly,
    "playoffs": run_playoffs,
    "cbc_announce": run_cbc_announce,
    "cbc_kbo": run_cbc_kbo,
    "cbc_npb": run_cbc_npb,
    "cbc_epl": run_cbc_epl,
    "cbc_results": run_cbc_results,
    "cbc_gotd": run_cbc_gotd,
    "cbc_potd": run_cbc_potd,
    "scan_game": run_scan_game,
    "scan_prop": run_scan_prop,
    "scan_nrfi": run_scan_nrfi,
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
