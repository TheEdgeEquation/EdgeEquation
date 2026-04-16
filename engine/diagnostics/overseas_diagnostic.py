import logging
from datetime import date

from engine.international_scrapers import (
    scrape_kbo_schedule,
    _get_kbo_espn_fallback,
    scrape_npb_schedule,
    _get_npb_espn_fallback,
)

from engine.global_router import get_projections
from engine.global_game_factory import build_game_list

logger = logging.getLogger(__name__)


def run_overseas_diagnostic(game_date: date = None):
    if game_date is None:
        game_date = date.today()

    print("\n==============================")
    print(" OVERSEAS DIAGNOSTIC REPORT")
    print("==============================\n")
    print(f"Date: {game_date}\n")

    # ─────────────────────────────────────────────
    # KBO OFFICIAL
    # ─────────────────────────────────────────────
    print("▶ KBO OFFICIAL SCRAPER")
    kbo_official = scrape_kbo_schedule(game_date)
    print(f"  Games found: {len(kbo_official)}")
    print(f"  Sample: {kbo_official[:2]}\n")

    # ─────────────────────────────────────────────
    # KBO ESPN FALLBACK
    # ─────────────────────────────────────────────
    print("▶ KBO ESPN FALLBACK")
    kbo_espn = _get_kbo_espn_fallback(game_date)
    print(f"  Games found: {len(kbo_espn)}")
    print(f"  Sample: {kbo_espn[:2]}\n")

    # ─────────────────────────────────────────────
    # NPB OFFICIAL
    # ─────────────────────────────────────────────
    print("▶ NPB OFFICIAL SCRAPER")
    npb_official = scrape_npb_schedule(game_date)
    print(f"  Games found: {len(npb_official)}")
    print(f"  Sample: {npb_official[:2]}\n")

    # ─────────────────────────────────────────────
    # NPB ESPN FALLBACK
    # ─────────────────────────────────────────────
    print("▶ NPB ESPN FALLBACK")
    npb_espn = _get_npb_espn_fallback(game_date)
    print(f"  Games found: {len(npb_espn)}")
    print(f"  Sample: {npb_espn[:2]}\n")

    # ─────────────────────────────────────────────
    # ROUTER OUTPUT
    # ─────────────────────────────────────────────
    print("▶ ROUTER OUTPUT (KBO)")
    kbo_router = get_projections("kbo", game_date)
    print(f"  Games found: {len(kbo_router)}")
    print(f"  Sample: {kbo_router[:2]}\n")

    print("▶ ROUTER OUTPUT (NPB)")
    npb_router = get_projections("npb", game_date)
    print(f"  Games found: {len(npb_router)}")
    print(f"  Sample: {npb_router[:2]}\n")

    # ─────────────────────────────────────────────
    # FACTORY OUTPUT
    # ─────────────────────────────────────────────
    print("▶ FACTORY OUTPUT (KBO)")
    kbo_factory = build_game_list(kbo_router)
    print(f"  Games built: {len(kbo_factory)}")
    print(f"  Sample: {kbo_factory[:2]}\n")

    print("▶ FACTORY OUTPUT (NPB)")
    npb_factory = build_game_list(npb_router)
    print(f"  Games built: {len(npb_factory)}")
    print(f"  Sample: {npb_factory[:2]}\n")

    # ─────────────────────────────────────────────
    # POSTING READINESS
    # ─────────────────────────────────────────────
    print("▶ POSTING READINESS")
    print(f"  KBO ready: {len(kbo_factory) > 0}")
    print(f"  NPB ready: {len(npb_factory) > 0}")

    print("\n==============================")
    print(" END OF DIAGNOSTIC")
    print("==============================\n")
