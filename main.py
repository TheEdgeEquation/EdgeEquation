import argparse
import logging
from email_sender import send_email
from engine.email_builder import build_daily_brief


from datetime import datetime

from engine.edge_calculator import grade_all_props, calculate_nrfi_plays
from engine.prizepicks_scraper import fetch_prizepicks_props
from engine.results_checker import (
    check_mlb_results,
    check_pitcher_results,
    check_global_results,
)
from engine.content_generators import (
    generate_gotd_from_play,
    generate_potd_from_play,
    generate_first_inning_from_play,
    generate_results_post,
    generate_called_it_post,
    generate_daily_accuracy_post,
    caption_weekly,
)
from engine.global_accuracy import (
    evaluate_global_results,
    generate_global_accuracy_post,
)
from engine.social import post_tweet
from engine.stats_tracker import (
    build_weekly_stats,
    build_all_time_stats,
)
from engine.utils import game_has_started, get_daily_cta

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ============================================================
# INGESTION + FILTERS
# ============================================================

def _fetch_props():
    logger.info("Fetching props (PrizePicks validated)...")
    props = fetch_prizepicks_props() or []

    if not props:
        logger.warning("No PrizePicks props returned — using empty list")
        return []

    return props


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
        if p.get("prop_label") not in (
            "K", "NRFI", "YRFI", "3PM", "PTS", "SOG", "AST", "REB"
        )
    ]


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


def run_daily_email(dry_run, no_graphic):
    logger.info("MODE: daily_email")

    try:
        # Core projections
        from engine.projectors.mlb_games import get_mlb_game_projections
        from engine.projectors.mlb_pitchers import get_mlb_pitcher_projections
        from engine.projectors.nba_games import get_nba_game_projections
        from engine.projectors.nhl_games import get_nhl_game_projections

        # NRFI/YRFI engine
        nrfi_plays = calculate_nrfi_plays() or []

        # Personalization engines
        from engine.personal_engine import (
            build_personal_parlay,
            build_personal_prizepicks_card,
        )

        # Bankroll + all-time stats
        from engine.data_tracker import get_bankroll_summary
        all_time = build_all_time_stats(style="ee")

        # Build projections
        mlb_games = get_mlb_game_projections()
        mlb_pitchers = get_mlb_pitcher_projections()
        nba_games = get_nba_game_projections()
        nhl_games = get_nhl_game_projections()

        # Personal cards
        personal_parlay = build_personal_parlay()
        personal_pp = build_personal_prizepicks_card()

        bankroll = get_bankroll_summary()

        # ---------------------------------------------------------
        # 1) GRAPHIC PROMPT + PICKS INSIDE THE GRAPHIC (B graphic)
        # ---------------------------------------------------------
        # For now, we build a simple text version using NRFI/YRFI
        # and any other plays you decide to include.
        # You can later swap this for your dedicated graphic prompt builder.
        first_inning_lines = []
        for p in nrfi_plays:
            label = p.get("prop_label")
            book = p.get("book", "PrizePicks")
            team = p.get("team") or p.get("game_id", "Unknown game")
            edge = p.get("edge", 0)
            first_inning_lines.append(
                f"{label} | {team} | {book} | edge={edge:.3f}"
            )

        graphic_picks_text = "\n".join(first_inning_lines)

        graphic_prompt_text = "\n".join([
            "EDGE EQUATION — DAILY",
            "",
            "Sections:",
            "• First Inning Plays (NRFI/YRFI)",
            "• Long Ball Alerts (HR props)",
            "• The Outlier",
            "• Smash of the Day",
            "• Sharp Signal",
            "",
            "Use the picks listed below to populate each section.",
        ])

        # ---------------------------------------------------------
        # 2) ENGINE ACCURACY (INTERNAL) + 3) PUBLIC ACCURACY
        # ---------------------------------------------------------
        # For now, we keep these as placeholders until we refactor
        # the results pipeline to return structured stats instead of tweets.
        engine_accuracy_text = (
            "Engine accuracy section placeholder.\n"
            "Wire this to your results/graded plays pipeline when ready."
        )

        public_accuracy_text = (
            "Public accuracy section placeholder.\n"
            "Wire this to your public-pick tracking when ready."
        )

        # ---------------------------------------------------------
        # 4) PERSONAL PARLAY
        # ---------------------------------------------------------
        personal_parlay_text = str(personal_parlay)

        # ---------------------------------------------------------
        # 5) PERSONAL TOP 10 GRADED PICKS (WITH LETTER GRADES)
        # ---------------------------------------------------------
        # You can refine this grading logic later; for now we sort by edge.
        all_plays = _sort_by_edge(_load_all_today_plays())
        personal_top10 = all_plays[:10]

        def _grade(edge: float) -> str:
            if edge >= 0.12:
                return "A"
            if edge >= 0.08:
                return "B"
            if edge >= 0.05:
                return "C"
            if edge >= 0.02:
                return "D"
            return "F"

        personal_top10_lines = []
        for i, p in enumerate(personal_top10, start=1):
            edge = p.get("edge", 0.0)
            grade = _grade(edge)
            desc = p.get("description") or p.get("prop_label") or "Play"
            personal_top10_lines.append(
                f"{i}. {desc} — edge={edge:.3f} — Grade {grade}"
            )

        personal_top10_text = "\n".join(personal_top10_lines)

        # ---------------------------------------------------------
        # 6) TOP 10 PROPS (WITH LETTER GRADES)
        # ---------------------------------------------------------
        prop_plays = _filter_props(all_plays)
        top10_props = prop_plays[:10]

        prop_top10_lines = []
        for i, p in enumerate(top10_props, start=1):
            edge = p.get("edge", 0.0)
            grade = _grade(edge)
            desc = p.get("description") or p.get("prop_label") or "Prop"
            prop_top10_lines.append(
                f"{i}. {desc} — edge={edge:.3f} — Grade {grade}"
            )

        prop_top10_text = "\n".join(prop_top10_lines)

        # ---------------------------------------------------------
        # 7) FULL PUBLIC CARD (ALL PICKS BEING POSTED TODAY)
        # ---------------------------------------------------------
        # For now, we mirror the personal top plays; you can later
        # restrict this to only the subset you actually post.
        public_card_lines = []
        for p in personal_top10:
            edge = p.get("edge", 0.0)
            desc = p.get("description") or p.get("prop_label") or "Play"
            public_card_lines.append(f"{desc} — edge={edge:.3f}")

        public_card_text = "\n".join(public_card_lines)

        # ---------------------------------------------------------
        # BUILD EMAIL BODY
        # ---------------------------------------------------------
        body = build_daily_brief(
            graphic_prompt_text=graphic_prompt_text,
            graphic_picks_text=graphic_picks_text,
            engine_accuracy_text=engine_accuracy_text,
            public_accuracy_text=public_accuracy_text,
            personal_parlay_text=personal_parlay_text,
            personal_top10_text=personal_top10_text,
            prop_top10_text=prop_top10_text,
            public_card_text=public_card_text,
        )

        if not dry_run:
            send_email(
                subject="Edge Equation — Daily Intelligence Brief",
                body=body,
            )
            logger.info("Daily intelligence brief email sent")
        else:
            logger.info("[DRY RUN] Daily intelligence brief generated:\n" + body)

    except Exception as e:
        logger.error("Daily email failed: " + str(e))



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

        caption = "EDGE EQUATION — FIRST INNING POTD\n\n" + fi_text

        if not dry_run:
            post_tweet(caption)
            logger.info("First Inning POTD posted")
        else:
            logger.info("[DRY RUN] First Inning POTD:\n" + caption)

    except Exception as e:
        logger.error("First Inning POTD failed: " + str(e))


def run_daily(dry_run, no_graphic):
    logger.info("MODE: daily")
    try:
        plays = _sort_by_edge(_load_all_today_plays())
        plays = [p for p in plays if not game_has_started(p)]

        game_plays = _filter_games(plays)
        prop_plays = _filter_props(plays)
        nrfi_plays = _filter_nrfi(plays)

        top_game = game_plays[0] if game_plays else None
        top_prop = prop_plays[0] if prop_plays else None
        top_nrfi = nrfi_plays[0] if nrfi_plays else None

        caption_lines = ["EDGE EQUATION — DAILY CARD", ""]

        if top_game:
            gotd_text = generate_gotd_from_play(top_game)
            caption_lines.append("GAME OF THE DAY")
            caption_lines.append(gotd_text)
            caption_lines.append("")

        if top_prop:
            potd_text = generate_potd_from_play(top_prop)
            caption_lines.append("PROP OF THE DAY")
            caption_lines.append(potd_text)
            caption_lines.append("")

        if top_nrfi:
            fi_text = generate_first_inning_from_play(top_nrfi)
            caption_lines.append("FIRST INNING POTD")
            caption_lines.append(fi_text)
            caption_lines.append("")

        caption_lines.append(get_daily_cta())
        caption_lines.append("#EdgeEquation")

        caption = "\n".join(caption_lines)

        if not dry_run:
            post_tweet(caption)
            logger.info("Daily card posted")
        else:
            logger.info("[DRY RUN] Daily card:\n" + caption)

    except Exception as e:
        logger.error("Daily failed: " + str(e))


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

        text = generate_gotd_from_play(top_game)
        caption = "EDGE EQUATION — GAME OF THE DAY\n\n" + text

        if not dry_run:
            post_tweet(caption)
            logger.info("GOTD posted")
        else:
            logger.info("[DRY RUN] GOTD:\n" + caption)

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

        text = generate_potd_from_play(top_prop)
        caption = "EDGE EQUATION — PROP OF THE DAY\n\n" + text

        if not dry_run:
            post_tweet(caption)
            logger.info("POTD posted")
        else:
            logger.info("[DRY RUN] POTD:\n" + caption)

    except Exception as e:
        logger.error("POTD failed: " + str(e))


def run_results(dry_run, no_graphic):
    logger.info("MODE: results")
    try:
        from engine.results_loader import get_todays_graded_plays

        todays_plays = get_todays_graded_plays() or []

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
                post_tweet(called_it)

            accuracy = generate_daily_accuracy_post(
                game_hits, game_misses,
                pitcher_hits, pitcher_misses
            )
            if accuracy:
                post_tweet(accuracy)

        else:
            logger.info("[DRY RUN] Accuracy calculated")

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
    caption = (
        "EDGE EQUATION — Monthly Summary\n\n"
        f"Total graded outputs: {stats.get('total', 0)}"
    )

    if not dry_run:
        post_tweet(caption)
    else:
        logger.info("[DRY RUN] Monthly:\n" + caption)


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
        plays = [p for p in plays if not game_has_started(p)]

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
        plays = [p for p in plays if not game_has_started(p)]

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
        plays = [p for p in plays if not game_has_started(p)]

        game_plays = _filter_games(plays)
        low_total_games = [
            p for p in game_plays
            if p.get("market") == "total" and p.get("edge", 0) < 0
        ]

        top_game = low_total_games[0] if low_total_games else None

        if not top_game:
            logger.info("No run suppression edges found")
            return

        text = generate_gotd_from_play(top_game)
        caption = "EDGE EQUATION 3.0 — RUN SUPPRESSION SIGNAL\n\n" + text

        logger.info("[DRY RUN] Run Suppression Signal:\n" + caption)

    except Exception as e:
        logger.error("Run Suppression Signal failed: " + str(e))


def run_high_confidence_outlier(dry_run, no_graphic):
    logger.info("MODE: high_confidence_outlier")
    try:
        plays = _sort_by_edge(_load_all_today_plays())
        plays = [p for p in plays if not game_has_started(p)]

        strong_edges = [p for p in plays if p.get("edge", 0) >= 0.10]
        top_play = strong_edges[0] if strong_edges else None

        if not top_play:
            logger.info("No high-confidence outliers found")
            return

        if top_play.get("prop_label") in ("K", "HITS", "TOTAL_BASES", "HOME_RUNS"):
            text = generate_potd_from_play(top_play)
        else:
            text = generate_gotd_from_play(top_play)

        caption = "EDGE EQUATION 3.0 — HIGH CONFIDENCE OUTLIER\n\n" + text

        logger.info("[DRY RUN] High Confidence Outlier:\n" + caption)

    except Exception as e:
        logger.error("High Confidence Outlier failed: " + str(e))


def run_secondary_alignment(dry_run, no_graphic):
    logger.info("MODE: secondary_alignment")
    try:
        plays = _sort_by_edge(_load_all_today_plays())
        plays = [p for p in plays if not game_has_started(p)]

        game_plays = _filter_games(plays)
        prop_plays = _filter_props(plays)

        aligned = []
        for g in game_plays:
            for p in prop_plays:
                if (
                    g.get("game_id") == p.get("game_id")
                    and g.get("side") == p.get("side")
                ):
                    aligned.append((g, p))

        if not aligned:
            logger.info("No secondary alignment edges found")
            return

        top_game, top_prop = aligned[0]

        game_text = generate_gotd_from_play(top_game)
        prop_text = generate_potd_from_play(top_prop)

        caption = "\n".join([
            "EDGE EQUATION 3.0 — SECONDARY ALIGNMENT",
            "",
            "GAME EDGE",
            game_text,
            "",
            "PROP EDGE",
            prop_text,
        ])

        logger.info("[DRY RUN] Secondary Alignment:\n" + caption)

    except Exception as e:
        logger.error("Secondary Alignment failed: " + str(e))


# ============================================================
# EDGE EQUATION 3.0 — GLOBAL SIGNAL MODES
# ============================================================

def run_global_primary_signal(dry_run, no_graphic):
    logger.info("MODE: global_primary_signal")
    try:
        plays = _sort_by_edge(_load_all_today_plays())
        plays = [
            p for p in plays
            if p.get("sport") in ("kbo", "npb", "soccer_epl", "soccer_ucl")
            and not game_has_started(p)
        ]

        game_plays = _filter_games(plays)
        top_game = game_plays[0] if game_plays else None

        if not top_game:
            logger.info("No global game-level edges for Primary Signal")
            return

        text = generate_gotd_from_play(top_game)
        caption = "EDGE EQUATION GLOBAL — PRIMARY SIGNAL\n\n" + text

        logger.info("[DRY RUN] Global Primary Signal:\n" + caption)

    except Exception as e:
        logger.error("Global Primary Signal failed: " + str(e))


def run_global_prop_efficiency_signal(dry_run, no_graphic):
    logger.info("MODE: global_prop_efficiency_signal")
    try:
        plays = _sort_by_edge(_load_all_today_plays())
        plays = [
            p for p in plays
            if p.get("sport") in ("kbo", "npb", "soccer_epl", "soccer_ucl")
            and not game_has_started(p)
        ]

        prop_plays = _filter_props(plays)
        top_prop = prop_plays[0] if prop_plays else None

        if not top_prop:
            logger.info("No global prop edges for Prop Efficiency Signal")
            return

        text = generate_potd_from_play(top_prop)
        caption = "EDGE EQUATION GLOBAL — PROP EFFICIENCY SIGNAL\n\n" + text

        logger.info("[DRY RUN] Global Prop Efficiency Signal:\n" + caption)

    except Exception as e:
        logger.error("Global Prop Efficiency Signal failed: " + str(e))


def run_global_run_suppression_signal(dry_run, no_graphic):
    logger.info("MODE: global_run_suppression_signal")
    try:
        plays = _sort_by_edge(_load_all_today_plays())
        plays = [
            p for p in plays
            if p.get("sport") in ("kbo", "npb", "soccer_epl", "soccer_ucl")
            and not game_has_started(p)
        ]

        game_plays = _filter_games(plays)
        low_total_games = [
            p for p in game_plays
            if p.get("market") == "total" and p.get("edge", 0) < 0
        ]

        top_game = low_total_games[0] if low_total_games else None

        if not top_game:
            logger.info("No global run suppression edges found")
            return

        text = generate_gotd_from_play(top_game)
        caption = "EDGE EQUATION GLOBAL — RUN SUPPRESSION SIGNAL\n\n" + text

        logger.info("[DRY RUN] Global Run Suppression Signal:\n" + caption)

    except Exception as e:
        logger.error("Global Run Suppression Signal failed: " + str(e))


def run_global_high_confidence_outlier(dry_run, no_graphic):
    logger.info("MODE: global_high_confidence_outlier")
    try:
        plays = _sort_by_edge(_load_all_today_plays())
        plays = [
            p for p in plays
            if p.get("sport") in ("kbo", "npb", "soccer_epl", "soccer_ucl")
            and not game_has_started(p)
        ]

        strong_edges = [p for p in plays if p.get("edge", 0) >= 0.10]
        top_play = strong_edges[0] if strong_edges else None

        if not top_play:
            logger.info("No global high-confidence outliers found")
            return

        if top_play.get("prop_label") in ("HITS", "TOTAL_BASES", "HOME_RUNS"):
            text = generate_potd_from_play(top_play)
        else:
            text = generate_gotd_from_play(top_play)

        caption = "EDGE EQUATION GLOBAL — HIGH CONFIDENCE OUTLIER\n\n" + text

        logger.info("[DRY RUN] Global High Confidence Outlier:\n" + caption)

    except Exception as e:
        logger.error("Global High Confidence Outlier failed: " + str(e))


def run_global_secondary_alignment(dry_run, no_graphic):
    logger.info("MODE: global_secondary_alignment")
    try:
        plays = _sort_by_edge(_load_all_today_plays())
        plays = [
            p for p in plays
            if p.get("sport") in ("kbo", "npb", "soccer_epl", "soccer_ucl")
            and not game_has_started(p)
        ]

        game_plays = _filter_games(plays)
        prop_plays = _filter_props(plays)

        aligned = []
        for g in game_plays:
            for p in prop_plays:
                if (
                    g.get("game_id") == p.get("game_id")
                    and g.get("side") == p.get("side")
                ):
                    aligned.append((g, p))

        if not aligned:
            logger.info("No global secondary alignment edges found")
            return

        top_game, top_prop = aligned[0]

        game_text = generate_gotd_from_play(top_game)
        prop_text = generate_potd_from_play(top_prop)

        caption = "\n".join([
            "EDGE EQUATION GLOBAL — SECONDARY ALIGNMENT",
            "",
            "GAME EDGE",
            game_text,
            "",
            "PROP EDGE",
            prop_text,
        ])

        logger.info("[DRY RUN] Global Secondary Alignment:\n" + caption)

    except Exception as e:
        logger.error("Global Secondary Alignment failed: " + str(e))


# ============================================================
# MODES DICTIONARY — 3.0 ALIGNED
# ============================================================

MODES_US_3 = {
    "model_notes": run_model_notes,
    "primary_signal": run_primary_signal,
    "prop_efficiency_signal": run_prop_efficiency_signal,
    "run_suppression_signal": run_run_suppression_signal,
    "high_confidence_outlier": run_high_confidence_outlier,
    "secondary_alignment": run_secondary_alignment,
}

MODES_GLOBAL_3 = {
    "global_primary_signal": run_global_primary_signal,
    "global_prop_efficiency_signal": run_global_prop_efficiency_signal,
    "global_run_suppression_signal": run_global_run_suppression_signal,
    "global_high_confidence_outlier": run_global_high_confidence_outlier,
    "global_secondary_alignment": run_global_secondary_alignment,
}

MODES_LEGACY = {
    "daily_email": run_daily_email,
    "system_status": run_system_status,
    "daily": run_daily,
    "gotd": run_gotd,
    "potd": run_potd,
    "first_inning_potd": run_first_inning_potd,
    "results": run_results,
    "weekly": run_weekly,
    "monthly": run_monthly,
}

MODES = {
    **MODES_US_3,
    **MODES_GLOBAL_3,
    **MODES_LEGACY,
}


# ============================================================
# MODE SIGNATURE VALIDATION
# ============================================================

import inspect


def validate_modes():
    for mode_name, fn in MODES.items():
        if not callable(fn):
            raise TypeError(f"Mode '{mode_name}' is not callable")

        sig = inspect.signature(fn)
        params = sig.parameters

        required = ["dry_run", "no_graphic"]

        for r in required:
            if r not in params:
                raise TypeError(
                    f"Mode '{mode_name}' must accept '{r}' as a parameter"
                )

        for r in required:
            p = params[r]
            if p.kind not in (p.KEYWORD_ONLY, p.POSITIONAL_OR_KEYWORD):
                raise TypeError(
                    f"Mode '{mode_name}' parameter '{r}' must be keyword-compatible"
                )


validate_modes()


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
