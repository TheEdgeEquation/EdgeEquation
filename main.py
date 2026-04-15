import argparse
import logging
import sys
import time
from datetime import datetime, timezone

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
from engine.cbc_projector import (
    get_epl_projections, get_ucl_projections,
)
from engine.gotd_generator import generate_gotd_from_play, generate_potd_from_play, generate_first_inning_from_play
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
    Fetch props with retry logic.
    """
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
    return [p for p in plays if p.get("prop_label") in ("K", "SOG", "3PM", "PTS", "AST", "REB")]


def _filter_nrfi(plays):
    return [p for p in plays if p.get("prop_label") in ("NRFI", "YRFI")]


def _filter_games(plays):
    return [
        p for p in plays
        if p.get("prop_label") not in ("K", "NRFI", "YRFI", "3PM", "PTS", "SOG", "AST", "REB")
    ]
    # ============================================================
# LEGACY MODES (ESSENTIAL ONLY)
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
        props = _fetch_props()
        graded = grade_all_props(props) if props else []
        nrfi = calculate_nrfi_plays() or []
        all_plays = graded + nrfi

        if not all_plays:
            logger.info("No plays for GOTD")
            return

        all_plays.sort(key=lambda x: -x.get("edge", 0))

        game_plays = _filter_games(all_plays)
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
        props = _fetch_props()
        graded = grade_all_props(props) if props else []
        nrfi = calculate_nrfi_plays() or []
        all_plays = graded + nrfi

        if not all_plays:
            logger.info("No plays for POTD")
            return

        all_plays.sort(key=lambda x: -x.get("edge", 0))

        prop_plays = _filter_props(all_plays)
        top_prop = prop_plays[0] if prop_plays else None

        if top_prop:
            post_text = generate_potd_from_play(top_prop)
            if post_text:
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
        # US projections
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

        # Overseas projections
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

        # Accuracy breakdown
        from engine.data_tracker import load_plays
        todays_plays = load_plays(_today(), "ee")

        mlb_game_projs = [
            p for p in todays_plays
            if p.get("sport") == "baseball_mlb" and p.get("prop_label") not in ("K", "NRFI", "YRFI")
        ]
        pitcher_projs = [p for p in todays_plays if p.get("prop_label") == "K"]

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
                game_hits, game_misses, pitcher_hits, pitcher_misses
            )
            if accuracy:
                post_tweet(accuracy)

        else:
            logger.info("[DRY RUN] Accuracy calculated")

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


# ============================================================
# SCAN MODES (B)
# ============================================================

def run_scan_game(dry_run, no_graphic):
    logger.info("MODE: scan_game")
    mlb = get_mlb_game_projections()
    nba = get_nba_game_projections()
    nhl = get_nhl_game_projections()
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


# ============================================================
# REMINDER MODES
# ============================================================

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
# EDGE EQUATION 3.0 — US SIGNAL MODES
# ============================================================

def run_model_notes(dry_run, no_graphic):
    logger.info("MODE: model_notes")

    weekly = build_weekly_stats(style="ee")
    all_time = build_all_time_stats(style="ee")

    caption = "\n".join([
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
    ])

    logger.info("[DRY RUN] Model Notes:\n" + caption)


def run_primary_signal(dry_run, no_graphic):
    logger.info("MODE: primary_signal")
    try:
        plays = _sort_by_edge(_load_all_today_plays())
        game_plays = _filter_games(plays)
        top_game = game_plays[0] if game_plays else None

        if not top_game:
            logger.info("No game-level edges for Primary Signal")
            return

        text = generate_gotd_from_play(top_game)
        caption = "EDGE EQUATION 3.0 — PRIMARY SIGNAL\n\n" + text

        logger.info("[DRY RUN] Primary Signal:\n" + caption)

    except Exception as e:
        logger.error("Primary Signal failed: " + str(e))


def run_prop_efficiency_signal(dry_run, no_graphic):
    logger.info("MODE: prop_efficiency_signal")
    try:
        plays = _sort_by_edge(_load_all_today_plays())
        prop_plays = _filter_props(plays)
        top_prop = prop_plays[0] if prop_plays else None

        if not top_prop:
            logger.info("No prop edges for Prop Efficiency Signal")
            return

        text = generate_potd_from_play(top_prop)
        caption = "EDGE EQUATION 3.0 — PROP EFFICIENCY SIGNAL\n\n" + text

        logger.info("[DRY RUN] Prop Efficiency Signal:\n" + caption)

    except Exception as e:
        logger.error("Prop Efficiency Signal failed: " + str(e))


def run_run_suppression_signal(dry_run, no_graphic):
    logger.info("MODE: run_suppression_signal")
    try:
        plays = _sort_by_edge(_load_all_today_plays())
        nrfi_plays = _filter_nrfi(plays)
        top_nrfi = nrfi_plays[0] if nrfi_plays else None

        if not top_nrfi:
            logger.info("No NRFI/YRFI edges for Run Suppression Signal")
            return

        text = generate_first_inning_from_play(top_nrfi)
        caption = "EDGE EQUATION 3.0 — RUN SUPPRESSION SIGNAL\n\n" + text

        logger.info("[DRY RUN] Run Suppression Signal:\n" + caption)

    except Exception as e:
        logger.error("Run Suppression Signal failed: " + str(e))


def run_high_confidence_outlier(dry_run, no_graphic):
    logger.info("MODE: high_confidence_outlier")
    try:
        plays = _sort_by_edge(_load_all_today_plays())
        top_play = plays[0]

        if top_play.get("prop_label") in ("K", "SOG", "3PM", "PTS", "AST", "REB"):
            text = generate_potd_from_play(top_play)
        else:
            text = generate_gotd_from_play(top_play)

        caption = "EDGE EQUATION 3.0 — HIGH-CONFIDENCE OUTLIER\n\n" + text

        logger.info("[DRY RUN] High-Confidence Outlier:\n" + caption)

    except Exception as e:
        logger.error("High-Confidence Outlier failed: " + str(e))


def run_secondary_alignment(dry_run, no_graphic):
    logger.info("MODE: secondary_alignment")
    try:
        plays = _sort_by_edge(_load_all_today_plays())
        if len(plays) < 2:
            logger.info("Not enough plays for Secondary Alignment")
            return

        second = plays[1]

        if second.get("prop_label") in ("K", "SOG", "3PM", "PTS", "AST", "REB"):
            text = generate_potd_from_play(second)
        else:
            text = generate_gotd_from_play(second)

        caption = "EDGE EQUATION 3.0 — SECONDARY ALIGNMENT\n\n" + text

        logger.info("[DRY RUN] Secondary Alignment:\n" + caption)

    except Exception as e:
        logger.error("Secondary Alignment failed: " + str(e))


# ============================================================
# EDGE EQUATION 3.0 — GLOBAL (OVERNIGHT) SIGNAL MODES
# ============================================================

def _load_global_games():
    """
    Loads KBO, NPB, EPL, UCL projections.
    """
    kbo = get_kbo_projections()
    npb = get_npb_projections()
    epl = get_epl_projections()
    ucl = get_ucl_projections()
    return kbo + npb + epl + ucl


def _filter_started_global(games):
    safe = []
    for g in games:
        if game_has_started(g):
            logger.info(f"Skipping {g.get('matchup')} — already started or final")
        else:
            safe.append(g)
    return safe


def _validate_global(g):
    if not g.get("vegas_total"):
        return False
    if g.get("model_total") == g.get("vegas_total"):
        return False
    return True


def run_global_primary_signal(dry_run, no_graphic):
    logger.info("MODE: global_primary_signal")

    games = _filter_started_global(_load_global_games())
    games = [g for g in games if _validate_global(g)]

    if not games:
        logger.info("No global games available")
        return

    games.sort(key=lambda x: -abs(x.get("model_total", 0) - x.get("vegas_total", 0)))
    top = games[0]

    text = generate_gotd_from_play(top)
    caption = "EDGE EQUATION 3.0 — GLOBAL PRIMARY SIGNAL\n\n" + text

    logger.info("[DRY RUN] Global Primary Signal:\n" + caption)


def run_global_prop_efficiency_signal(dry_run, no_graphic):
    logger.info("MODE: global_prop_efficiency_signal")

    plays = _sort_by_edge(_load_all_today_plays())
    props = _filter_props(plays)

    if not props:
        logger.info("No global props available")
        return

    top = props[0]
    text = generate_potd_from_play(top)
    caption = "EDGE EQUATION 3.0 — GLOBAL PROP EFFICIENCY SIGNAL\n\n" + text

    logger.info("[DRY RUN] Global Prop Efficiency Signal:\n" + caption)


def run_global_run_suppression_signal(dry_run, no_graphic):
    logger.info("MODE: global_run_suppression_signal")

    plays = _sort_by_edge(_load_all_today_plays())
    nrfi = _filter_nrfi(plays)

    if not nrfi:
        logger.info("No global NRFI/YRFI plays")
        return

    top = nrfi[0]
    text = generate_first_inning_from_play(top)
    caption = "EDGE EQUATION 3.0 — GLOBAL RUN SUPPRESSION SIGNAL\n\n" + text

    logger.info("[DRY RUN] Global Run Suppression Signal:\n" + caption)


def run_global_high_confidence_outlier(dry_run, no_graphic):
    logger.info("MODE: global_high_confidence_outlier")

    plays = _sort_by_edge(_load_all_today_plays())
    top = plays[0]

    if top.get("prop_label") in ("K", "SOG", "3PM", "PTS", "AST", "REB"):
        text = generate_potd_from_play(top)
    else:
        text = generate_gotd_from_play(top)

    caption = "EDGE EQUATION 3.0 — GLOBAL HIGH-CONFIDENCE OUTLIER\n\n" + text

    logger.info("[DRY RUN] Global High-Confidence Outlier:\n" + caption)


def run_global_secondary_alignment(dry_run, no_graphic):
    logger.info("MODE: global_secondary_alignment")

    plays = _sort_by_edge(_load_all_today_plays())
    if len(plays) < 2:
        logger.info("Not enough global plays")
        return

    second = plays[1]

    if second.get("prop_label") in ("K", "SOG", "3PM", "PTS", "AST", "REB"):
        text = generate_potd_from_play(second)
    else:
        text = generate_gotd_from_play(second)

    caption = "EDGE EQUATION 3.0 — GLOBAL SECONDARY ALIGNMENT\n\n" + text

    logger.info("[DRY RUN] Global Secondary Alignment:\n" + caption)


# ============================================================
# EDGE EQUATION 3.0 — DAILY EMAIL MODE
# ============================================================

def run_daily_email(dry_run, no_graphic):
    logger.info("MODE: daily_email")

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
    except Exception:
        personal_parlay = None

    personal_pp = build_personal_prizepicks(all_plays)
    bankroll = get_bankroll_summary()
    all_time = build_all_time_stats(style="ee")

    logger.info("[DRY RUN] Daily email would be sent")


# ============================================================
# MODES DICTIONARY — 3.0 FIRST
# ============================================================

MODES = {
    # 3.0 US Suite
    "model_notes": run_model_notes,
    "primary_signal": run_primary_signal,
    "prop_efficiency_signal": run_prop_efficiency_signal,
    "run_suppression_signal": run_run_suppression_signal,
    "high_confidence_outlier": run_high_confidence_outlier,
    "secondary_alignment": run_secondary_alignment,

    # 3.0 Global Suite
    "global_primary_signal": run_global_primary_signal,
    "global_prop_efficiency_signal": run_global_prop_efficiency_signal,
    "global_run_suppression_signal": run_global_run_suppression_signal,
    "global_high_confidence_outlier": run_global_high_confidence_outlier,
    "global_secondary_alignment": run_global_secondary_alignment,

    # Daily email
    "daily_email": run_daily_email,

    # Essential legacy modes
    "system_status": run_system_status,
    "daily": run_daily,
    "gotd": run_gotd,
    "potd": run_potd,
    "first_inning_potd": run_first_inning_potd,
    "results": run_results,
    "weekly": run_weekly,
    "monthly": run_monthly,

    # Scan modes
    "scan_game": run_scan_game,
    "scan_prop": run_scan_prop,
    "scan_nrfi": run_scan_nrfi,

    # Reminders
    "weekly_reminder": run_weekly_reminder,
    "monthly_reminder": run_monthly_reminder,
    "phase2": run_phase2,
    "phase3": run_phase3,
    "phase4": run_phase4,
}


# ============================================================
# MAIN
# ============================================================

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


