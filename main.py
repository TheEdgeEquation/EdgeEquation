import argparse
import logging
import sys
import time
from datetime import datetime, timezone
import inspect

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

# ============================================================
# ENGINE IMPORTS
# ============================================================

from engine.edge_calculator import grade_all_props, calculate_nrfi_plays
from engine.data_tracker import save_plays, build_weekly_stats, build_all_time_stats, save_results
from engine.score_checker import check_all_results
from engine.email_sender import send_projections_only_email, send_results_email
from engine.parlay_engine import build_game_parlay, build_prizepicks_parlay
from engine.personal_engine import build_personal_parlay, build_personal_prizepicks
from engine.kelly_calculator import apply_kelly_to_plays, get_bankroll_summary
from engine.content_generator import (
    generate_mlb_projection_post, generate_pitcher_projection_post,
    generate_nba_projection_post, generate_nhl_projection_post,
    generate_nrfi_probability_post, generate_results_post,
    generate_kbo_projection_post, generate_npb_projection_post,
    generate_epl_projection_post, generate_ucl_projection_post,
    get_daily_cta,
)
from engine.closing_line_tracker import track_clv_for_plays, generate_clv_post
from engine.game_projector import (
    get_mlb_game_projections, get_nba_game_projections,
    get_nhl_game_projections, get_mlb_pitcher_projections,
)
from engine.kbo_scraper import get_kbo_projections
from engine.npb_scraper import get_npb_projections
from engine.cbc_projector import get_epl_projections, get_ucl_projections
from engine.gotd_generator import (
    generate_gotd_from_play,
    generate_potd_from_play,
    generate_first_inning_from_play
)
from post_to_x import post_tweet, caption_weekly
from engine.highlight_generator import (
    check_mlb_results, check_pitcher_results,
    generate_called_it_post, generate_daily_accuracy_post,
)

# ============================================================
# EDGE EQUATION 3.0 — GLOBAL GAME START GUARDRAIL
# ============================================================

def game_has_started(play):
    """
    Returns True if the game has started or finished.
    Works for all sports and all projection types.
    """
    status = (play.get("status") or "").lower()

    if status in ("in_progress", "live", "final", "completed"):
        return True

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

# ============================================================
# HELPERS
# ============================================================

def _today():
    return datetime.now().strftime("%Y%m%d")

def _fetch_props():
    """
    3.0 — PrizePicks-only, validated prop ingestion.
    Removes retry logic and old generators.
    """
    from engine.prizepicks_scraper import fetch_prizepicks_props

    logger.info("Fetching props (PrizePicks validated)...")
    props = fetch_prizepicks_props() or []

    if not props:
        logger.warning("No PrizePicks props returned — using empty list")
        return []

    return props

# ============================================================
# EDGE EQUATION 3.0 — SIGNAL SELECTION LAYER
# ============================================================

def _load_all_today_plays():
    """
    Loads props + NRFI plays for both US and global signals.
    """
    props = _fetch_props()
    graded_props = grade_all_props(props) if props else []
    nrfi_plays = calculate_nrfi_plays() or []
    return graded_props + nrfi_plays

def _sort_by_edge(plays):
    return sorted(plays, key=lambda x: -x.get("edge", 0))

def _filter_props(plays):
    return [
        p for p in plays
        if p.get("prop_label") not in ("NRFI", "YRFI")
    ]

def _filter_nrfi(plays):
    return [p for p in plays if p.get("prop_label") in ("NRFI", "YRFI")]

def _filter_games(plays):
    return [
        p for p in plays
        if p.get("prop_label") not in ("K", "NRFI", "YRFI", "3PM", "PTS", "SOG", "AST", "REB")
        # ============================================================
# LEGACY MODES (CLEAN + STABLE)
# ============================================================

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
        "KBO  |  NPB  |  EPL  |  UCL",
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
        nrfi_plays = [p for p in nrfi_plays if not game_has_started(p)]

        if not nrfi_plays:
            logger.info("No NRFI/YRFI plays available")
            return

        nrfi_plays.sort(key=lambda x: -x.get("edge", 0))
        top_nrfi = nrfi_plays[0]

        fi_text = generate_first_inning_from_play(top_nrfi)
        if not fi_text:
            logger.warning("First Inning POTD generation returned empty")
            return

        if not dry_run:
            post_tweet(fi_text)
            logger.info("First Inning POTD posted")
        else:
            logger.info("[DRY RUN] First Inning POTD:\n" + fi_text)

    except Exception as e:
        logger.error("First Inning POTD failed: " + str(e))


def run_gotd(dry_run, no_graphic):
    logger.info("MODE: gotd")
    try:
        plays = _sort_by_edge(_load_all_today_plays())
        plays = [p for p in plays if not game_has_started(p)]

        game_plays = _filter_games(plays)
        top_game = game_plays[0] if game_plays else None

        if not top_game:
            logger.info("No game-level edges for GOTD")
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
        plays = _sort_by_edge(_load_all_today_plays())
        plays = [p for p in plays if not game_has_started(p)]

        prop_plays = _filter_props(plays)
        top_prop = prop_plays[0] if prop_plays else None

        if not top_prop:
            logger.info("No prop edges for POTD")
            return

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

    props = _fetch_props()
    graded_props = grade_all_props(props) if props else []
    all_plays = graded_props + nrfi_plays

    if all_plays:
        all_plays = apply_kelly_to_plays(all_plays)
        save_plays(all_plays, "ee")
        all_plays = track_clv_for_plays(all_plays)

    # Guardrail
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

    # Validation
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

    # Build parlays
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
        if mlb_pitchers:
            post_tweet(generate_pitcher_projection_post(mlb_pitchers))
        if nba_games:
            post_tweet(generate_nba_projection_post(nba_games))
        if nhl_games:
            post_tweet(generate_nhl_projection_post(nhl_games))
        if nrfi_plays:
            post_tweet(generate_nrfi_probability_post(nrfi_plays))

        if kbo_games:
            post_tweet(generate_kbo_projection_post(kbo_games))
        if npb_games:
            post_tweet(generate_npb_projection_post(npb_games))
        if epl_games:
            post_tweet(generate_epl_projection_post(epl_games))
        if ucl_games:
            post_tweet(generate_ucl_projection_post(ucl_games))

        send_projections_only_email(
            mlb_games=mlb_games, mlb_pitchers=mlb_pitchers,
            nba_games=nba_games, nhl_games=nhl_games,
            nrfi_plays=nrfi_plays,
            personal_parlay=personal_parlay, personal_pp=personal_pp,
            bankroll_summary=bankroll, all_time_stats=all_time,
        )
        logger.info("Email sent")

    else:
        logger.info("[DRY RUN] Daily projections completed")


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
            else:
                logger.info("[DRY RUN] Results:\n" + results_text)

        from engine.data_tracker import load_plays
        todays_plays = load_plays(_today(), "ee")

        mlb_game_projs = [
            p for p in todays_plays
            if p.get("sport") == "baseball_mlb"
            and p.get("prop_label") not in ("K", "NRFI", "YRFI")
        ]

        pitcher_projs = [
            p for p in todays_plays
            if p.get("prop_label") == "K"
        ]

        game_hits, game_misses = check_mlb_results(mlb_game_projs)
        pitcher_hits, pitcher_misses = check_pitcher_results(pitcher_projs)

        if not dry_run:
            called_it = generate_called_it_post(pitcher_hits, "pitcher")
            if called_it:
                post_tweet(called_it)

            called_it_game = generate_called_it_post(game_hits, "game")
            if called_it_game:
                post_tweet(called_it_game)

            accuracy = generate_daily_accuracy_post(
                game_hits, game_misses,
                pitcher_hits, pitcher_misses
            )
            if accuracy:
                post_tweet(accuracy)

        else:
            logger.info("[DRY RUN] Accuracy calculated")

        from engine.global_accuracy import (
            evaluate_global_results,
            generate_global_accuracy_post
        )

        global_plays = [
            p for p in todays_plays
            if p.get("sport") in ("kbo", "npb", "soccer_epl", "soccer_ucl")
        ]

        global_stats = evaluate_global_results(global_plays)

        if not dry_run:
            global_accuracy_post = generate_global_accuracy_post(global_stats)
            if global_accuracy_post:
                post_tweet(global_accuracy_post)
        else:
            logger.info("[DRY RUN] Global accuracy:\n" + str(global_stats))

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
    else:
        logger.info("[DRY RUN] Weekly:\n" + caption)


def run_monthly(dry_run, no_graphic):
    logger.info("MODE: monthly")
    stats = build_all_time_stats(style="ee")
    caption = f"EDGE EQUATION — Monthly Summary\n\nTotal graded outputs: {stats.get('total', 0)}"

    if not dry_run:
        post_tweet(caption)
    else:
        logger.info("[DRY RUN] Monthly:\n" + caption)

    ]
