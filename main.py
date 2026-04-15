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
from engine.email_sender import send_projections_only_email, send_results_email, _send
from engine.parlay_engine import build_game_parlay, build_prizepicks_parlay
from engine.personal_engine import build_personal_parlay, build_personal_prizepicks
from engine.kelly_calculator import apply_kelly_to_plays, get_bankroll_summary
from engine.analysis_generator import generate_all_analysis
from engine.content_generator import generate_results_post, generate_no_play_post, get_daily_cta
from engine.reminder_generator import generate_daily_todo
from engine.closing_line_tracker import track_clv_for_plays, generate_clv_post
from engine.game_projector import get_mlb_game_projections, get_nba_game_projections, get_nhl_game_projections, get_mlb_pitcher_projections
from engine.playoff_projector import get_nba_playoff_projections, get_nhl_playoff_projections, format_nba_playoff_post, format_nhl_playoff_post
from engine.cbc_projector import get_epl_projections, get_ucl_projections, get_kbo_projections, get_npb_projections, format_epl_projection_post, format_ucl_projection_post, format_kbo_projection_post, format_npb_projection_post, format_cbc_results_post
from engine.brand_validator import validate_or_abort
from engine.state_tracker import get_and_update, mark_posted, save_state
from engine.gotd_potd_generator import generate_gotd, generate_potd, find_top_game, find_top_prop
from engine.results_tracker import build_daily_summary, build_ytd_summary
from post_to_x import post_tweet, post_thread, caption_announce, caption_cbc_announce, caption_results_ee, caption_weekly, caption_no_play
 
SPORT_MAP = {
    "baseball_mlb": "MLB",
    "basketball_nba": "NBA",
    "icehockey_nhl": "NHL",
    "americanfootball_nfl": "NFL",
    "basketball_wnba": "WNBA",
    "americanfootball_ncaaf": "NCAAF",
    "basketball_ncaab": "NCAAB",
    "baseball_kbo": "KBO",
    "baseball_npb": "NPB",
    "soccer_epl": "EPL",
    "soccer_uefa_champs_league": "UCL",
}
 
 
def _today():
    return datetime.now().strftime("%Y%m%d")
 
 
def _normalize_sport(raw: str) -> str:
    return SPORT_MAP.get(raw, raw.upper())
 
 
def _post_safe(text, account, post_type, brand, state, dry_run):
    validated = validate_or_abort(text, post_type)
    if not validated:
        logger.warning(f"[{post_type}] Brand validation failed — aborted")
        return False
    if not dry_run:
        result = post_tweet(validated, account=account)
        if result:
            state = mark_posted(state, post_type)
            save_state(state)
            logger.info(f"[{post_type}] Posted successfully")
            return True
        return False
    else:
        logger.info(f"[DRY RUN] [{post_type}]:\n{validated}")
        return True
 
 
def _fetch_props():
    from engine.prop_generator import generate_all_props
    MAX_ATTEMPTS = 4
    WAIT_MINUTES = 5
    for attempt in range(1, MAX_ATTEMPTS + 1):
        logger.info("Fetch attempt " + str(attempt) + " of " + str(MAX_ATTEMPTS))
        try:
            props = generate_all_props() or []
            if props:
                return props
        except Exception as e:
            logger.error("Props failed: " + str(e))
        if attempt < MAX_ATTEMPTS:
            time.sleep(WAIT_MINUTES * 60)
    return []
 
 
def run_system_status(dry_run, no_graphic):
    logger.info("MODE: system_status")
    state = get_and_update()
    from engine.game_state_monitor import get_active_sports
    active = get_active_sports("EE")
    leagues = " · ".join(active) if active else "MLB · NBA · NHL"
    text = (
        f"Edge Equation — {datetime.now().strftime('%A, %B %d')}\n\n"
        f"Engine active. No picks. No advice.\n\n"
        f"Today's coverage: {leagues}\n\n"
        f"Projections publish after 11 AM CT.\n\n"
        f"#EdgeEquation #DataNotFeelings"
    )
    _post_safe(text, "ee", "system_status", "EE", state, dry_run)
 
 
def run_gotd(dry_run, no_graphic):
    logger.info("MODE: gotd")
    state = get_and_update()
    mlb_games = get_mlb_game_projections()
    top = find_top_game(mlb_games) if mlb_games else None
    if not top:
        logger.info("No GOTD — no qualifying games")
        return
    text = generate_gotd("MLB", top)
    if not text:
        logger.info("GOTD generation failed")
        return
    _post_safe(text[:280], "ee", "EE_gotd", "EE", state, dry_run)
 
 
def run_potd(dry_run, no_graphic):
    logger.info("MODE: potd")
    state = get_and_update()
    props = _fetch_props()
    if not props:
        logger.info("No POTD — no qualifying props")
        return
    top = find_top_prop(props)
    if not top:
        return
    sport = _normalize_sport(top.get("sport", "MLB"))
    text = generate_potd(sport, top)
    if not text:
        logger.info("POTD generation failed")
        return
    _post_safe(text[:280], "ee", "EE_potd", "EE", state, dry_run)
 
 
def run_announce(dry_run, no_graphic):
    logger.info("MODE: announce")
    state = get_and_update()
    caption = caption_announce()
    _post_safe(caption, "ee", "EE_projections", "EE", state, dry_run)
 
 
def run_daily(dry_run, no_graphic):
    logger.info("MODE: daily")
    state = get_and_update()
    mlb_games = get_mlb_game_projections()
    mlb_pitchers = get_mlb_pitcher_projections()
    nba_games = get_nba_game_projections()
    nhl_games = get_nhl_game_projections()
    nrfi_plays = calculate_nrfi_plays() or []
    logger.info(f"MLB={len(mlb_games)} Pitchers={len(mlb_pitchers)} NBA={len(nba_games)} NHL={len(nhl_games)} NRFI={len(nrfi_plays)}")
    props = _fetch_props()
    graded_props = grade_all_props(props) if props else []
    all_plays = graded_props + nrfi_plays
    if all_plays:
        all_plays = apply_kelly_to_plays(all_plays)
        save_plays(all_plays, "ee")
    if all_plays:
        all_plays = track_clv_for_plays(all_plays)
    clv_plays = [p for p in all_plays if p.get("clv", 0) > 0.01]
    clv_post = generate_clv_post(clv_plays) if clv_plays else None
    analyses, why_passed = generate_all_analysis(all_plays)
    try:
        from engine.parlay_engine import evaluate_game_for_parlay, get_todays_games
        game_bets = []
        for game in get_todays_games():
            bets = evaluate_game_for_parlay(game)
            game_bets.extend(bets)
        personal_parlay = build_personal_parlay(game_bets)
    except Exception as e:
        logger.error("Personal parlay failed: " + str(e))
        personal_parlay = None
    personal_pp = build_personal_prizepicks(all_plays)
    bankroll = get_bankroll_summary()
    all_time = build_all_time_stats(style="ee")
    from engine.content_generator import (
        generate_mlb_projection_post, generate_pitcher_projection_post,
        generate_nba_projection_post, generate_nhl_projection_post,
        generate_nrfi_probability_post,
    )
    if not dry_run:
        if mlb_games:
            _post_safe(generate_mlb_projection_post(mlb_games), "ee", "EE_projections", "EE", state, dry_run)
        if mlb_pitchers:
            _post_safe(generate_pitcher_projection_post(mlb_pitchers), "ee", "EE_projections", "EE", state, dry_run)
        if nba_games:
            _post_safe(generate_nba_projection_post(nba_games), "ee", "EE_projections", "EE", state, dry_run)
        if nhl_games:
            _post_safe(generate_nhl_projection_post(nhl_games), "ee", "EE_projections", "EE", state, dry_run)
        if nrfi_plays:
            _post_safe(generate_nrfi_probability_post(nrfi_plays), "ee", "nrfi", "EE", state, dry_run)
        if clv_post:
            _post_safe(clv_post, "ee", "EE_projections", "EE", state, dry_run)
        send_projections_only_email(
            mlb_games=mlb_games,
            mlb_pitchers=mlb_pitchers,
            nba_games=nba_games,
            nhl_games=nhl_games,
            nrfi_plays=nrfi_plays,
            personal_parlay=personal_parlay,
            personal_pp=personal_pp,
            bankroll_summary=bankroll,
            all_time_stats=all_time,
        )
        logger.info("Daily email sent")
    else:
        logger.info(f"[DRY RUN] Would post {sum([bool(mlb_games), bool(mlb_pitchers), bool(nba_games), bool(nhl_games), bool(nrfi_plays)])} projection posts")
        logger.info(f"[DRY RUN] Personal plays: parlay={bool(personal_parlay)} pp={bool(personal_pp)}")
 
 
def run_results(dry_run, no_graphic):
    logger.info("MODE: results")
    state = get_and_update()
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
        validated = validate_or_abort(results_text, "EE_results")
        if not validated:
            logger.warning("Results text failed brand validation")
            return
        if not dry_run:
            post_tweet(validated, account="ee")
            send_results_email(verified)
            state = mark_posted(state, "EE_results")
            save_state(state)
            logger.info("Results posted and emailed")
        else:
            logger.info(f"[DRY RUN] Results:\n{validated}")
    except Exception as e:
        logger.error("Results failed: " + str(e))
 
 
def run_weekly(dry_run, no_graphic):
    logger.info("MODE: weekly")
    state = get_and_update()
    stats = build_weekly_stats(style="ee")
    if stats["total"] == 0:
        logger.warning("No data for weekly roundup")
        return
    caption = caption_weekly(stats)
    _post_safe(caption, "ee", "EE_results", "EE", state, dry_run)
 
 
def run_playoffs(dry_run, no_graphic):
    logger.info("MODE: playoffs")
    state = get_and_update()
    nba = get_nba_playoff_projections()
    nhl = get_nhl_playoff_projections()
    nba_post = format_nba_playoff_post(nba)
    nhl_post = format_nhl_playoff_post(nhl)
    if not dry_run:
        if nba_post:
            _post_safe(nba_post, "ee", "EE_projections", "EE", state, dry_run)
        if nhl_post:
            _post_safe(nhl_post, "ee", "EE_projections", "EE", state, dry_run)
    else:
        logger.info(f"[DRY RUN] Playoffs:\n{nba_post}\n{nhl_post}")
 
 
def run_cbc_announce(dry_run, no_graphic):
    logger.info("MODE: cbc_announce")
    state = get_and_update()
    caption = caption_cbc_announce()
    _post_safe(caption, "cbc", "CBC_projections", "CBC", state, dry_run)
 
 
def run_cbc_kbo(dry_run, no_graphic):
    logger.info("MODE: cbc_kbo")
    state = get_and_update()
    projections = get_kbo_projections()
    post_text = format_kbo_projection_post(projections)
    if not post_text:
        logger.info("No KBO games today")
        return
    _post_safe(post_text, "cbc", "CBC_projections", "CBC", state, dry_run)
 
 
def run_cbc_npb(dry_run, no_graphic):
    logger.info("MODE: cbc_npb")
    state = get_and_update()
    projections = get_npb_projections()
    post_text = format_npb_projection_post(projections)
    if not post_text:
        logger.info("No NPB games today")
        return
    _post_safe(post_text, "cbc", "CBC_projections", "CBC", state, dry_run)
 
 
def run_cbc_epl(dry_run, no_graphic):
    logger.info("MODE: cbc_epl")
    state = get_and_update()
    epl = get_epl_projections()
    ucl = get_ucl_projections()
    if epl:
        _post_safe(format_epl_projection_post(epl), "cbc", "CBC_projections", "CBC", state, dry_run)
    if ucl:
        _post_safe(format_ucl_projection_post(ucl), "cbc", "CBC_projections", "CBC", state, dry_run)
    if not epl and not ucl:
        logger.info("No EPL/UCL games today")
 
 
def run_cbc_results(dry_run, no_graphic):
    logger.info("MODE: cbc_results")
    state = get_and_update()
    results_text = format_cbc_results_post([])
    _post_safe(results_text, "cbc", "CBC_results", "CBC", state, dry_run)
 
 
def run_cbc_gotd(dry_run, no_graphic):
    logger.info("MODE: cbc_gotd")
    state = get_and_update()
    kbo = get_kbo_projections()
    top = find_top_game(kbo) if kbo else None
    if not top:
        logger.info("No CBC GOTD today")
        return
    text = generate_gotd("KBO", top)
    if text:
        _post_safe(text[:280], "cbc", "CBC_gotd", "CBC", state, dry_run)
 
 
def run_cbc_potd(dry_run, no_graphic):
    logger.info("MODE: cbc_potd")
    state = get_and_update()
    logger.info("CBC POTD — no prop source configured yet")
 
 
def run_scan_game(dry_run, no_graphic):
    logger.info("MODE: scan_game")
    from engine.manual_scanner import scan_game, format_scan_email
    result = scan_game(
        sport="MLB",
        away="Yankees",
        home="Red Sox",
        proj_away=4.3,
        proj_home=5.6,
    )
    body = format_scan_email(result)
    subject = f"EE SCAN — Game | {datetime.now().strftime('%B %d %H:%M')}"
    if not dry_run:
        _send(subject, body)
        logger.info("Scan emailed")
    else:
        logger.info(f"[DRY RUN] Scan result:\n{body}")
 
 
def run_scan_prop(dry_run, no_graphic):
    logger.info("MODE: scan_prop")
    from engine.manual_scanner import scan_prop, format_scan_email
    result = scan_prop(
        sport="MLB",
        player="Gerrit Cole",
        prop_type="Strikeouts",
        proj_value=7.2,
        vegas_line=6.5,
        vegas_juice=-130,
    )
    body = format_scan_email(result)
    subject = f"EE SCAN — Prop | {datetime.now().strftime('%B %d %H:%M')}"
    if not dry_run:
        _send(subject, body)
        logger.info("Scan emailed")
    else:
        logger.info(f"[DRY RUN] Scan result:\n{body}")
 
 
def run_scan_nrfi(dry_run, no_graphic):
    logger.info("MODE: scan_nrfi")
    from engine.manual_scanner import scan_nrfi, format_scan_email
    result = scan_nrfi(
        away="Yankees",
        home="Red Sox",
        away_era=3.2,
        home_era=3.8,
    )
    body = format_scan_email(result)
    subject = f"EE SCAN — NRFI | {datetime.now().strftime('%B %d %H:%M')}"
    if not dry_run:
        _send(subject, body)
        logger.info("Scan emailed")
    else:
        logger.info(f"[DRY RUN] Scan result:\n{body}")
 
 
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
    parser = argparse.ArgumentParser(description="EdgeEquation + CBC Runner")
    parser.add_argument("--mode", required=True, choices=list(MODES.keys()))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-graphic", action="store_true")
    args = parser.parse_args()
    logger.info("Starting | mode=" + args.mode + " | dry_run=" + str(args.dry_run))
    MODES[args.mode](dry_run=args.dry_run, no_graphic=args.no_graphic)
    logger.info("Run complete.")
 
 
if __name__ == "__main__":
    main()
