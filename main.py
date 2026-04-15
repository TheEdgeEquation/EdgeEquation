import argparse
import logging
import sys
import time
from datetime import datetime

# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

# ---------------------------------------------------------
# Imports — unchanged from your existing system
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# NEW PLAYOFF ENGINE IMPORTS
# ---------------------------------------------------------
from engine.playoff_engine import project_series
from engine.playoff_matchups import NBA_PLAYOFF_MATCHUPS, NHL_PLAYOFF_MATCHUPS
from engine.playoff_formatter import format_league_overview, format_all_matchups

# ---------------------------------------------------------
# Other engines
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# MODES — unchanged logic, cleaner structure
# ---------------------------------------------------------

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
    logger.info("[DRY RUN]" if dry_run else "System status posted")


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
        logger.info("[DRY RUN]" if dry_run else "GOTD posted")

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
            if not dry_run:
                post_tweet(post_text)
            logger.info("[DRY RUN]" if dry_run else "POTD posted")

        if top_nrfi:
            fi_text = generate_first_inning_from_play(top_nrfi)
            if not dry_run:
                post_tweet(fi_text)
            logger.info("[DRY RUN]" if dry_run else "First Inning Spotlight posted")

    except Exception as e:
        logger.error("POTD failed: " + str(e))


def run_announce(dry_run, no_graphic):
    logger.info("MODE: announce")
    caption = caption_announce()
    if not dry_run:
        post_tweet(caption)
    logger.info("[DRY RUN]" if dry_run else "Announce posted")


# ---------------------------------------------------------
# DAILY MODE — unchanged logic
# ---------------------------------------------------------
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
        if clv_post:
            post_tweet(clv_post)

        send_projections_only_email(
            mlb_games=mlb_games, mlb_pitchers=mlb_pitchers,
            nba_games=nba_games, nhl_games=nhl_games,
            nrfi_plays=nrfi_plays,
            personal_parlay=personal_parlay, personal_pp=personal_pp,
            bankroll_summary=bankroll, all_time_stats=all_time,
        )
    else:
        logger.info("[DRY RUN] Daily mode executed")


# ---------------------------------------------------------
# RESULTS MODE — unchanged logic
# ---------------------------------------------------------
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

        logger.info("Checking game projections vs actuals...")
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

            accuracy = generate_daily_accuracy_post(game_hits, game_misses, pitcher_hits, pitcher_misses)
            if accuracy:
                post_tweet(accuracy)
        else:
            logger.info("[DRY RUN] Results mode executed")

    except Exception as e:
        logger.error("Results failed: " + str(e))


# ---------------------------------------------------------
# WEEKLY MODE — unchanged
# ---------------------------------------------------------
def run_weekly(dry_run, no_graphic):
    logger.info("MODE: weekly")
    stats = build_weekly_stats(style="ee")
    if stats["total"] == 0:
        logger.warning("No data for weekly roundup")
        return
    caption = caption_weekly(stats)
    if not dry_run:
        post_tweet(caption)
    logger.info("[DRY RUN]" if dry_run else "Weekly posted")


# ---------------------------------------------------------
# **NEW CLEAN PLAYOFF MODE**
# ---------------------------------------------------------
def run_playoffs(dry_run, no_graphic):
    logger.info("MODE: playoffs")

    # NBA
    nba_projections = [
        project_series(m["higher_seed"], m["lower_seed"], m["conference"], "nba")
        for m in NBA_PLAYOFF_MATCHUPS
    ]
    nba_overview = format_league_overview("nba")
    nba_posts = format_all_matchups(nba_projections)

    # NHL
    nhl_projections = [
        project_series(m["higher_seed"], m["lower_seed"], m["conference"], "nhl")
        for m in NHL_PLAYOFF_MATCHUPS
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
        logger.info("[DRY RUN] NHL Overview:\n" + nhl_overview)


# ---------------------------------------------------------
# CBC MODES — unchanged
# ---------------------------------------------------------
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
    logger.info("[DRY RUN]" if dry_run else "CBC announce posted")


def run_cbc_kbo(dry_run, no_graphic):
    logger.info("MODE: cbc_kbo")
    projections = get_kbo_projections()
    post_text = format_kbo_projection_post(projections)
    if not post_text:
        logger.info("No KBO games today")
        return
    if not dry_run:
        post_tweet(post_text)
    logger.info("[DRY RUN]" if dry_run else "KBO posted")


def run_cbc_npb(dry_run, no_graphic):
    logger.info("MODE: cbc_npb")
    projections = get_npb_projections()
    post_text = format_npb_projection_post(projections)
    if not post_text:
        logger.info("No NPB games today")
        return
    if not dry_run:
        post_tweet(post_text)
    logger.info("[DRY RUN]" if dry_run else "NPB posted")


def run_cbc_epl(dry_run, no_graphic):
    logger.info("MODE: cbc_epl")
    epl = get_epl_projections()
    ucl = get_ucl_projections()
    if epl:
        post_text = format_epl_projection_post(epl)
        if not dry_run:
            post_tweet(post_text)
    if ucl:
        post_text = format_ucl_projection_post(ucl)
        if not dry_run:
            post_tweet(post_text)
    if not epl and not ucl:
        logger.info("No EPL/UCL games today")
    logger.info("[DRY RUN]" if dry_run else "CBC EPL/UCL posted")


def run_cbc_results(dry_run, no_graphic):
    logger.info("MODE: cbc_results")
    results_text = format_cbc_results_post([])
    if not dry_run:
        post_tweet(results_text)
    logger.info("[DRY RUN]" if dry_run else "CBC results posted")


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
                "Market
