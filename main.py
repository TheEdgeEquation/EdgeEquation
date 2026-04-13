import argparse
import logging
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("main")

from engine.odds_fetcher import fetch_all_props
from engine.edge_calculator import grade_all_props
from engine.data_tracker import save_plays, load_plays, save_results, load_results, build_weekly_stats
from engine.visualizer import generate_main_graphic, generate_announce_graphic, generate_results_graphic, generate_weekly_graphic, generate_cbc_tease_graphic
from engine.score_checker import check_all_results
from engine.sms_sender import send_picks_sms, format_picks_for_sms
from post_to_x import post_tweet, caption_announce, caption_daily_ee, caption_results_ee, caption_cbc_tease, caption_cbc_drop, caption_cbc_results, caption_weekly


def _today():
    return datetime.now().strftime("%Y%m%d")


def _fetch_and_grade(style="ee"):
    logger.info("Fetching props from Odds API...")
    props = fetch_all_props()
    if not props:
        logger.warning("No props returned from API")
        return []
    logger.info("Running Monte Carlo on " + str(len(props)) + " props...")
    plays = grade_all_props(props)
    if not plays:
        logger.warning("No plays met threshold")
        return []
    save_plays(plays, style)
    logger.info(str(len(plays)) + " plays saved")
    return plays


def _build_announce_games():
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
            games.append({"sport_label": p["sport_label"], "home": p["team"], "away": p["opponent"], "time": time_str})
    return games[:12]


def run_announce(dry_run, no_graphic):
    logger.info("MODE: announce")
    games = _build_announce_games()
    sports = list({g["sport_label"] for g in games})
    date_str = datetime.now().strftime("%A, %B %d")
    sport_str = "  |  ".join(sports) if sports else "MLB  |  NHL  |  NBA"
    caption = (
        "📋 " + date_str + " — Games we are scanning today.\n\n"
        "Markets: " + sport_str + "\n"
        "Props: Pitcher Ks  •  Player 3s  •  SOG  •  Receptions\n\n"
        "A+/A/A- plays drop at 10:30 AM CDT.\n\n"
        "Live data. 100% Ver
