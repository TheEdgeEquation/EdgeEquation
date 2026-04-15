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
from engine.kbo_scraper import get_kbo_projections
from engine.npb_scraper import get_npb_projections
from engine.cbc_projector import (
    get_epl_projections, get_ucl_projections,
    format_epl_projection_post, format_ucl_projection_post,
    format_kbo_projection_post, format_npb_projection_post,
    format_cbc_results_post,
)
from engine.gotd_generator import generate_gotd_from_play, generate_potd_from_play, generate_first_inning_from_play
from post_to_x import post_tweet, caption_announce, caption_results_ee, caption_weekly
from engine.highlight_generator import (
    check_mlb_results, check_pitcher_results,
    generate_called_it_post, generate_miss_post,
    generate_daily_accuracy_post,
)

# NEW: playoff engine + auto bracket
from engine.playoff_engine import project_series
from engine.playoff_formatter import format_league_overview, format_all_matchups
from engine.bracket_auto import get_nba_playoff_matchups, get_nhl_playoff_matchups
# ============================================================
# EDGE EQUATION 3.0 — GLOBAL GAME START GUARDRAIL
# ============================================================

from datetime import timezone

def game_has_started(play):
    """
    Returns True if the game has started or finished.
    Works for all sports and all projection types.
    """
    status = (play.get("status") or "").lower()

    # If API already marks it as live or final
    if status in ("in_progress", "live", "final", "completed"):
        return True

    # Try to read start time
    start = play.get("start_time") or play.get("game_time")
    if not start:
        return False

    try:
        if isinstance(start, str):
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        else:
            start_dt = start

        now = datetime.now(timezone.utc)
        return now >= start_dt
    except Exception:
        return False



def _today():
    return datetime.now().strftime("%Y%m%d")


def _fetch_props():
    from engine.prop_generator import generate_all_props
    for attempt in range(1, 5):
        logger.info(f"Fetch attempt {attempt} of 4")
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
        f"EDGE EQUATION — {date_str}",
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

def run_first_inning_potd(dry_run, no_graphic):
    logger.info("MODE: first_inning_potd")
    try:
        nrfi_plays = calculate_nrfi_plays() or []

        if not nrfi_plays:
            logger.info("No NRFI/YRFI plays available for First Inning POTD")
            return

        # Sort by edge descending
        nrfi_plays.sort(key=lambda x: -x.get("edge", 0))
        top_nrfi = nrfi_plays[0]

        fi_text = generate_first_inning_from_play(top_nrfi)
        if not fi_text:
            logger.warning("First Inning POTD generation returned empty")
            return

        if not dry_run:
            post_tweet(fi_text)
            logger.info("First Inning Play of the Day posted")
        else:
            logger.info("[DRY RUN] First Inning POTD:\n" + fi_text)

    except Exception as e:
        logger.error("First Inning POTD failed: " + str(e))

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

        game_plays = [
            p for p in all_plays
            if p.get("prop_label") not in ("K", "NRFI", "YRFI", "3PM", "PTS", "SOG", "AST", "REB")
        ]
        top_game = game_plays[0] if game_plays else None

        if not top_game:
            logger.info("No game total plays for GOTD today")
            return

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
        nrfi = calculate_nrfi_plays() or []
        all_plays = graded + nrfi

        if not all_plays:
            logger.info("No plays for POTD/First Inning")
            return

        all_plays.sort(key=lambda x: -x.get("edge", 0))

        prop_plays = [p for p in all_plays if p.get("prop_label") in ("K", "SOG", "3PM", "PTS", "AST", "REB")]
        top_prop = prop_plays[0] if prop_plays else None

        nrfi_plays = [p for p in all_plays if p.get("prop_label") in ("NRFI", "YRFI")]
        top_nrfi = nrfi_plays[0] if nrfi_plays else None

        if top_prop:
            post_text = generate_potd_from_play(top_prop)
            if post_text:
                if not dry_run:
                    post_tweet(post_text)
                    logger.info("POTD posted")
                else:
                    logger.info("[DRY RUN] POTD:\n" + post_text)

        if top_nrfi:
            fi_text = generate_first_inning_from_play(top_nrfi)
            if fi_text:
                if not dry_run:
                    post_tweet(fi_text)
                    logger.info("First Inning Spotlight posted")
                else:
                    logger.info("[DRY RUN] First Inning Spotlight:\n" + fi_text)

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
        f"MLB={len(mlb_games)} NBA={len(nba_games)} NHL={len(nhl_games)} "
        f"KBO={len(kbo_games)} NPB={len(npb_games)} EPL={len(epl_games)}"
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
    # ============================================================
    # EDGE EQUATION 3.0 — APPLY GLOBAL GAME START GUARDRAIL
    # ============================================================

    def filter_started(games):
        safe = []
        for g in games:
            if game_has_started(g):
                logger.info(f"Skipping {g.get('matchup')} — already started or final")
            else:
                safe.append(g)
        return safe

    mlb_games = filter_started(mlb_games)
    mlb_pitchers = filter_started(mlb_pitchers)
    nba_games = filter_started(nba_games)
    nhl_games = filter_started(nhl_games)
    kbo_games = filter_started(kbo_games)
    npb_games = filter_started(npb_games)
    epl_games = filter_started(epl_games)
    ucl_games = filter_started(ucl_games)
        # ============================================================
    # EDGE EQUATION 3.0 — VALIDATION LAYER
    # ============================================================

    def validate_projection(g):
        if not g.get("vegas_total"):
            logger.info(f"Skipping {g.get('matchup')} — missing Vegas line")
            return False
        if g.get("model_total") == g.get("vegas_total"):
            logger.info(f"Skipping {g.get('matchup')} — duplicated model/market values")
            return False
        return True

    mlb_games = [g for g in mlb_games if validate_projection(g)]
    nba_games = [g for g in nba_games if validate_projection(g)]
    nhl_games = [g for g in nhl_games if validate_projection(g)]


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
        logger.info(f"[DRY RUN] Would post {posts} projection posts to X")
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
        verified = [r for r in results if r.get("result_checked")] if results else []
        if verified:
            save_results(verified, style="ee")
            results_text = generate_results_post(verified)
            if not dry_run:
                post_tweet(results_text)
                send_results_email(verified)
                logger.info("Results posted and emailed")
            else:
                logger.info("[DRY RUN] Results:\n" + results_text)

        logger.info("Checking game projections vs actuals...")
        try:
            from engine.data_tracker import load_plays
            todays_plays = load_plays(_today(), "ee")
            mlb_game_projs = [
                p for p in todays_plays
                if p.get("sport") == "baseball_mlb" and p.get("prop_label") not in ("K", "NRFI", "YRFI")
            ]
            pitcher_projs = [p for p in todays_plays if p.get("prop_label") == "K"]
            game_hits, game_misses = check_mlb_results(mlb_game_projs)
            pitcher_hits, pitcher_misses = check_pitcher_results(pitcher_projs)
            logger.info(f"Game hits: {len(game_hits)} misses: {len(game_misses)}")
            logger.info(f"Pitcher hits: {len(pitcher_hits)} misses: {len(pitcher_misses)}")
            if not dry_run:
                called_it = generate_called_it_post(pitcher_hits, "pitcher")
                if called_it:
                    post_tweet(called_it)
                    logger.info("Called it post sent")
                called_it_game = generate_called_it_post(game_hits, "game")
                if called_it_game:
                    post_tweet(called_it_game)
                    logger.info("Called it game post sent")
                accuracy = generate_daily_accuracy_post(game_hits, game_misses, pitcher_hits, pitcher_misses)
                if accuracy:
                    post_tweet(accuracy)
                    logger.info("Accuracy report posted")
            else:
                if pitcher_hits:
                    logger.info("[DRY RUN] Called it:\n" + generate_called_it_post(pitcher_hits, "pitcher"))
                accuracy = generate_daily_accuracy_post(game_hits, game_misses, pitcher_hits, pitcher_misses)
                logger.info("[DRY RUN] Accuracy:\n" + accuracy)
        except Exception as e:
            logger.error("Highlight generation failed: " + str(e))
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

    # NBA
    nba_matchups = get_nba_playoff_matchups()
    nba_projections = [
        project_series(m["higher_seed"], m["lower_seed"], m["conference"], "nba")
        for m in nba_matchups
    ]
    nba_overview = format_league_overview("nba")
    nba_posts = format_all_matchups(nba_projections)

    # NHL
    nhl_matchups = get_nhl_playoff_matchups()
    nhl_projections = [
        project_series(m["higher_seed"], m["lower_seed"], m["conference"], "nhl")
        for m in nhl_matchups
    ]
    nhl_overview = format_league_overview("nhl")
    nhl_posts = format_all_matchups(nhl_projections)

    if not dry_run:
        post_tweet(nba_overview)
        for p in nba_posts:
            post_tweet(p)
        post_tweet(nhl_overview)
        for p in nhl_posts:
            post_tweet(p)
        logger.info("Playoff threads posted")
    else:
        logger.info("[DRY RUN] NBA Overview:\n" + nba_overview)
        for p in nba_posts:
            logger.info("[DRY RUN] NBA Matchup:\n" + p)
        logger.info("[DRY RUN] NHL Overview:\n" + nhl_overview)
        for p in nhl_posts:
            logger.info("[DRY RUN] NHL Matchup:\n" + p)


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
    logger.info(f"Scan complete: MLB={len(mlb)} NBA={len(nba)} NHL={len(nhl)}")


def run_scan_prop(dry_run, no_graphic):
    logger.info("MODE: scan_prop")
    props = _fetch_props()
    graded = grade_all_props(props) if props else []
    logger.info(f"Scan complete: {len(graded)} props graded")


def run_scan_nrfi(dry_run, no_graphic):
    logger.info("MODE: scan_nrfi")
    nrfi = calculate_nrfi_plays() or []
    logger.info(f"Scan complete: {len(nrfi)} NRFI/YRFI plays")


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
    # ============================================================
# EDGE EQUATION 3.0 — SIGNAL SELECTION LAYER
# ============================================================

def _load_all_today_plays():
    """
    Helper to load all today's plays (props + NRFI) using existing pipeline.
    Reuses _fetch_props + grade_all_props + calculate_nrfi_plays.
    """
    props = _fetch_props()
    graded_props = grade_all_props(props) if props else []
    nrfi_plays = calculate_nrfi_plays() or []
    all_plays = graded_props + nrfi_plays
    return all_plays


def _sort_by_edge(plays):
    return sorted(plays, key=lambda x: -x.get("edge", 0))


def _filter_props(plays):
    return [p for p in plays if p.get("prop_label") in ("K", "SOG", "3PM", "PTS", "AST", "REB")]


def _filter_nrfi(plays):
    return [p for p in plays if p.get("prop_label") in ("NRFI", "YRFI")]


def _filter_games(plays):
    return [
        p for p in plays
        if p.get("prop_label") not in ("K", "NRFI", "YRFI", "3PM", "PTS", "SOG", "AST", "REB")
    ]
    # ============================================================
# EDGE EQUATION 3.0 — PUBLIC SIGNAL MODES
# ============================================================

def run_model_notes(dry_run, no_graphic):
    """
    Daily Model Notes — anchor post.
    For now, this is a simple placeholder using existing stats.
    Later we’ll wire this to a dedicated engine_tuning module.
    """
    logger.info("MODE: model_notes")

    # Simple version: pull weekly stats + all-time as context
    weekly = build_weekly_stats(style="ee")
    all_time = build_all_time_stats(style="ee")

    lines = [
        "EDGE EQUATION 3.0 — MODEL NOTES",
        "",
        f"Weekly volume: {weekly.get('total', 0)} graded outputs",
        f"All-time volume: {all_time.get('total', 0)} graded outputs",
        "",
        "Model continues to scan:",
        "• Scoring environments",
        "• Pace and shot volume",
        "• Volatility and late-game drift",
        "",
        "Always learning. Always refining.",
        "#EdgeEquation",
    ]
    caption = "\n".join(lines)

    if not dry_run:
        post_tweet(caption)
        logger.info("Model notes posted")
    else:
        logger.info("[DRY RUN] Model notes:\n" + caption)


def run_primary_signal(dry_run, no_graphic):
    """
    Primary Signal — top game-level edge.
    Reuses GOTD logic but with 3.0 naming and cleaner framing.
    """
    logger.info("MODE: primary_signal")
    try:
        all_plays = _load_all_today_plays()
        if not all_plays:
            logger.info("No plays available for Primary Signal")
            return

        all_plays = _sort_by_edge(all_plays)
        game_plays = _filter_games(all_plays)
        top_game = game_plays[0] if game_plays else None

        if not top_game:
            logger.info("No game-level edges for Primary Signal")
            return

        text = generate_gotd_from_play(top_game)
        if not text:
            logger.warning("Primary Signal generation returned empty")
            return

        # 3.0 framing: analytics, not picks
        header = "EDGE EQUATION 3.0 — PRIMARY SIGNAL"
        caption = header + "\n\n" + text

        if not dry_run:
            post_tweet(caption)
            logger.info("Primary Signal posted")
        else:
            logger.info("[DRY RUN] Primary Signal:\n" + caption)
    except Exception as e:
        logger.error("Primary Signal failed: " + str(e))


def run_prop_efficiency_signal(dry_run, no_graphic):
    """
    Prop Efficiency Signal — top prop edge.
    """
    logger.info("MODE: prop_efficiency_signal")
    try:
        all_plays = _load_all_today_plays()
        if not all_plays:
            logger.info("No plays available for Prop Efficiency Signal")
            return

        all_plays = _sort_by_edge(all_plays)
        prop_plays = _filter_props(all_plays)
        top_prop = prop_plays[0] if prop_plays else None

        if not top_prop:
            logger.info("No prop edges for Prop Efficiency Signal")
            return

        text = generate_potd_from_play(top_prop)
        if not text:
            logger.warning("Prop Efficiency Signal generation returned empty")
            return

        header = "EDGE EQUATION 3.0 — PROP EFFICIENCY SIGNAL"
        caption = header + "\n\n" + text

        if not dry_run:
            post_tweet(caption)
            logger.info("Prop Efficiency Signal posted")
        else:
            logger.info("[DRY RUN] Prop Efficiency Signal:\n" + caption)
    except Exception as e:
        logger.error("Prop Efficiency Signal failed: " + str(e))


def run_run_suppression_signal(dry_run, no_graphic):
    """
    Run Suppression Signal — top NRFI/YRFI edge.
    """
    logger.info("MODE: run_suppression_signal")
    try:
        all_plays = _load_all_today_plays()
        if not all_plays:
            logger.info("No plays available for Run Suppression Signal")
            return

        all_plays = _sort_by_edge(all_plays)
        nrfi_plays = _filter_nrfi(all_plays)
        top_nrfi = nrfi_plays[0] if nrfi_plays else None

        if not top_nrfi:
            logger.info("No NRFI/YRFI edges for Run Suppression Signal")
            return

        text = generate_first_inning_from_play(top_nrfi)
        if not text:
            logger.warning("Run Suppression Signal generation returned empty")
            return

        header = "EDGE EQUATION 3.0 — RUN SUPPRESSION SIGNAL"
        caption = header + "\n\n" + text

        if not dry_run:
            post_tweet(caption)
            logger.info("Run Suppression Signal posted")
        else:
            logger.info("[DRY RUN] Run Suppression Signal:\n" + caption)
    except Exception as e:
        logger.error("Run Suppression Signal failed: " + str(e))


def run_high_confidence_outlier(dry_run, no_graphic):
    """
    High-Confidence Outlier — single highest edge across all plays.
    """
    logger.info("MODE: high_confidence_outlier")
    try:
        all_plays = _load_all_today_plays()
        if not all_plays:
            logger.info("No plays available for High-Confidence Outlier")
            return

        all_plays = _sort_by_edge(all_plays)
        top_play = all_plays[0]

        # Reuse GOTD/POTD generator depending on type
        if top_play.get("prop_label") in ("K", "SOG", "3PM", "PTS", "AST", "REB"):
            text = generate_potd_from_play(top_play)
        else:
            text = generate_gotd_from_play(top_play)

        if not text:
            logger.warning("High-Confidence Outlier generation returned empty")
            return

        header = "EDGE EQUATION 3.0 — HIGH-CONFIDENCE OUTLIER"
        caption = header + "\n\n" + text

        if not dry_run:
            post_tweet(caption)
            logger.info("High-Confidence Outlier posted")
        else:
            logger.info("[DRY RUN] High-Confidence Outlier:\n" + caption)
    except Exception as e:
        logger.error("High-Confidence Outlier failed: " + str(e))


def run_secondary_alignment(dry_run, no_graphic):
    """
    Secondary Alignment — second-strongest edge.
    """
    logger.info("MODE: secondary_alignment")
    try:
        all_plays = _load_all_today_plays()
        if not all_plays or len(all_plays) < 2:
            logger.info("Not enough plays for Secondary Alignment")
            return

        all_plays = _sort_by_edge(all_plays)
        second_play = all_plays[1]

        if second_play.get("prop_label") in ("K", "SOG", "3PM", "PTS", "AST", "REB"):
            text = generate_potd_from_play(second_play)
        else:
            text = generate_gotd_from_play(second_play)

        if not text:
            logger.warning("Secondary Alignment generation returned empty")
            return

        header = "EDGE EQUATION 3.0 — SECONDARY ALIGNMENT"
        caption = header + "\n\n" + text

        if not dry_run:
            post_tweet(caption)
            logger.info("Secondary Alignment posted")
        else:
            logger.info("[DRY RUN] Secondary Alignment:\n" + caption)
    except Exception as e:
        logger.error("Secondary Alignment failed: " + str(e))
        # ============================================================
# EDGE EQUATION 3.0 — DAILY EMAIL MODE
# ============================================================

def run_daily_email(dry_run, no_graphic):
    """
    3.0 daily email:
    - Reuses existing projections + parlay + PrizePicks logic from run_daily
    - Does NOT post to X
    - Sends projections-only email (including parlay + PP)
    """
    logger.info("MODE: daily_email")

    logger.info("Fetching projections for email...")
    mlb_games = get_mlb_game_projections()
    mlb_pitchers = get_mlb_pitcher_projections()
    nba_games = get_nba_game_projections()
    nhl_games = get_nhl_game_projections()
    nrfi_plays = calculate_nrfi_plays() or []

    kbo_games = get_kbo_projections()
    npb_games = get_npb_projections()
    epl_games = get_epl_projections()
    ucl_games = get_ucl_projections()

    props = _fetch_props()
    graded_props = grade_all_props(props) if props else []
    all_plays = graded_props + nrfi_plays

    if all_plays:
        all_plays = apply_kelly_to_plays(all_plays)
        save_plays(all_plays, "ee")
        all_plays = track_clv_for_plays(all_plays)

    try:
        from engine.parlay_engine import evaluate_game_for_parlay, get_todays_games
        game_bets = []
        for game in get_todays_games():
            game_bets.extend(evaluate_game_for_parlay(game))
        personal_parlay = build_personal_parlay(game_bets)
    except Exception as e:
        logger.error("Personal parlay failed (email mode): " + str(e))
        personal_parlay = None

    personal_pp = build_personal_prizepicks(all_plays)
    bankroll = get_bankroll_summary()
    all_time = build_all_time_stats(style="ee")

    if not dry_run:
        send_projections_only_email(
            mlb_games=mlb_games, mlb_pitchers=mlb_pitchers,
            nba_games=nba_games, nhl_games=nhl_games,
            nrfi_plays=nrfi_plays,
            personal_parlay=personal_parlay, personal_pp=personal_pp,
            bankroll_summary=bankroll, all_time_stats=all_time,
        )
        logger.info("3.0 daily email sent")
    else:
        logger.info("[DRY RUN] 3.0 daily email would be sent")





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
    "first_inning_potd": run_first_inning_potd,
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
        "model_notes": run_model_notes,
    "primary_signal": run_primary_signal,
    "prop_efficiency_signal": run_prop_efficiency_signal,
    "run_suppression_signal": run_run_suppression_signal,
    "high_confidence_outlier": run_high_confidence_outlier,
    "secondary_alignment": run_secondary_alignment,
    "daily_email": run_daily_email,

}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=list(MODES.keys()))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-graphic", action="store_true")
    args = parser.parse_args()
    logger.info(f"Starting | mode={args.mode} | dry_run={args.dry_run}")
    MODES[args.mode](dry_run=args.dry_run, no_graphic=args.no_graphic)
    logger.info("Run complete.")


if __name__ == "__main__":
    main()
