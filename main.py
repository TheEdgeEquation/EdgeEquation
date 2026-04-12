"""
main.py — EdgeEquation + Cash Before Coffee Main Runner

Usage:
  python main.py --mode announce
  python main.py --mode daily
  python main.py --mode results
  python main.py --mode weekly
  python main.py --mode cash_tease
  python main.py --mode cash_drop
  python main.py --mode cash_results

Flags:
  --dry-run     Generate output but don't post to X
  --no-graphic  Skip graphic generation
"""
import argparse
import logging
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("main")

from engine.odds_fetcher import fetch_all_props
from engine.edge_calculator import grade_all_props
from engine.data_tracker import (
    save_plays, load_plays,
    save_results, load_results,
    build_weekly_stats,
)
from engine.visualizer import (
    generate_main_graphic,
    generate_announce_graphic,
    generate_results_graphic,
    generate_weekly_graphic,
    generate_cbc_tease_graphic,
)
from post_to_x import (
    post_tweet,
    caption_announce, caption_daily_ee, caption_results_ee,
    caption_cbc_tease, caption_cbc_drop, caption_cbc_results,
    caption_weekly,
)


def _today() -> str:
    return datetime.now().strftime("%Y%m%d")


def _fetch_and_grade(style: str = "ee") -> list[dict]:
    logger.info("Fetching props from Odds API...")
    props = fetch_all_props()

    if not props:
        logger.warning("No props returned from API — no plays today")
        return []

    logger.info(f"Running Monte Carlo on {len(props)} props...")
    plays = grade_all_props(props)

    if not plays:
        logger.warning("No plays met A+/A/A- threshold today")
        return []

    save_plays(plays, style)
    logger.info(f"{len(plays)} plays graded and saved")
    return plays


def _build_announce_games() -> list[dict]:
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
            games.append({
                "sport_label": p["sport_label"],
                "home": p["team"],
                "away": p["opponent"],
                "time": time_str,
            })
    return games[:12]


def run_announce(dry_run: bool, no_graphic: bool):
    logger.info("MODE: announce")
    games = _build_announce_games()

    graphic = None
    if not no_graphic:
        graphic = generate_announce_graphic(games, style="ee")

    caption = caption_announce(games)
    logger.info(f"Caption:\n{caption}")

    if not dry_run:
        post_tweet(caption, graphic)
    else:
        logger.info("[DRY RUN] Would post announce")


def run_daily(dry_run: bool, no_graphic: bool):
    logger.info("MODE: daily")
    plays = _fetch_and_grade(style="ee")

    if not plays:
        caption = (
            "No A+/A/A- plays identified today.\n\n"
            "The model runs 10,000 simulations per line. "
            "When there's no edge, we don't force plays.\n\n"
            "Live data. 100% Verified. No feelings. Just facts.\n\n"
            "#EdgeEquation #NoPlay"
        )
        if not dry_run:
            post_tweet(caption)
        return

    graphic = None
    if not no_graphic:
        graphic = generate_main_graphic(plays, style="ee")

    caption = caption_daily_ee(plays)
    logger.info(f"Caption:\n{caption}")

    if not dry_run:
        post_tweet(caption, graphic)
    else:
        logger.info("[DRY RUN] Would post announce)
