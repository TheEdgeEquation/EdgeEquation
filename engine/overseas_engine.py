# engine/overseas_engine.py

from __future__ import annotations

import argparse
import datetime as dt
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple

import requests

# ==========================
# CONFIG & CONSTANTS
# ==========================

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)

HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json, text/html"}

# TODO: Fill these with your canonical validator names
KBO_TEAM_MAP = {
    # "Official Name": "EdgeEquation Name",
    # "KT Wiz": "KT Wiz",
}

NPB_TEAM_MAP = {
    # "Official Name": "EdgeEquation Name",
    # "Yokohama DeNA BayStars": "Yokohama DeNA",
}

PINNACLE_TEAM_MAP = {
    # "Pinnacle Name": "EdgeEquation Name",
    # "KT Wiz": "KT Wiz",
}

# TODO: Replace with real endpoints
KBO_OFFICIAL_URL_TEMPLATE = "https://example.kbo.or.kr/schedule?date={date}"
NPB_OFFICIAL_URL_TEMPLATE = "https://example.yahoo.jp/npb/schedule?date={date}"

PINNACLE_API_URL_TEMPLATE = "https://example.pinnacle.com/api/baseball/{league}/odds?date={date}"
PINNACLE_WEB_JSON_URL_TEMPLATE = "https://example.pinnacle.com/web/json/baseball/{league}?date={date}"


# ==========================
# DATA MODELS
# ==========================

@dataclass
class GameSchedule:
    league: str
    date: dt.date
    home_team: str
    away_team: str
    start_time: Optional[dt.datetime]  # UTC or local; you decide
    status: str  # "scheduled", "postponed", etc.


@dataclass
class GameOdds:
    league: str
    date: dt.date
    home_team: str
    away_team: str
    moneyline_home: Optional[float] = None
    moneyline_away: Optional[float] = None
    total: Optional[float] = None
    total_over_price: Optional[float] = None
    total_under_price: Optional[float] = None
    runline_home: Optional[float] = None
    runline_home_price: Optional[float] = None
    runline_away: Optional[float] = None
    runline_away_price: Optional[float] = None
    source: str = "pinnacle_api"  # or "pinnacle_web"


@dataclass
class ProjectionGame:
    league: str
    date: dt.date
    home_team: str
    away_team: str
    start_time: Optional[dt.datetime]
    status: str
    moneyline_home: Optional[float]
    moneyline_away: Optional[float]
    total: Optional[float]
    total_over_price: Optional[float]
    total_under_price: Optional[float]
    runline_home: Optional[float]
    runline_home_price: Optional[float]
    runline_away: Optional[float]
    runline_away_price: Optional[float]
    # room for projections / CLV later


# ==========================
# UTILITIES
# ==========================

def _parse_date(date_str: Optional[str]) -> dt.date:
    if date_str:
        return dt.datetime.strptime(date_str, "%Y-%m-%d").date()
    return dt.date.today()


def _debug_print(debug: bool, *args):
    if debug:
        print(*args)


def _normalize_team(name: str, league: str) -> str:
    name = name.strip()
    if league.lower() == "kbo":
        return KBO_TEAM_MAP.get(name, name)
    if league.lower() == "npb":
        return NPB_TEAM_MAP.get(name, name)
    return name


def _normalize_pinnacle_team(name: str) -> str:
    name = name.strip()
    return PINNACLE_TEAM_MAP.get(name, name)


def _game_key(league: str, home: str, away: str, date: dt.date) -> Tuple[str, str, str, dt.date]:
    return (league.lower(), home.lower(), away.lower(), date)


# ==========================
# OFFICIAL SCHEDULE SCRAPERS
# ==========================

def fetch_kbo_official_schedule(target_date: dt.date, debug: bool = False) -> List[GameSchedule]:
    url = KBO_OFFICIAL_URL_TEMPLATE.format(date=target_date.strftime("%Y%m%d"))
    _debug_print(debug, f"[KBO OFFICIAL] GET {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        _debug_print(debug, f"[KBO OFFICIAL] Error: {e}")
        return []

    html = resp.text
    # TODO: parse HTML and extract games
    # This is a stub; replace with real parsing logic.
    games: List[GameSchedule] = []

    _debug_print(debug, f"[KBO OFFICIAL] Parsed games: {len(games)}")
    return games


def fetch_npb_official_schedule(target_date: dt.date, debug: bool = False) -> List[GameSchedule]:
    url = NPB_OFFICIAL_URL_TEMPLATE.format(date=target_date.strftime("%Y%m%d"))
    _debug_print(debug, f"[NPB OFFICIAL] GET {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        _debug_print(debug, f"[NPB OFFICIAL] Error: {e}")
        return []

    # TODO: parse JSON from Yahoo Japan (or similar)
    # This is a stub; replace with real parsing logic.
    data = resp.json()
    games: List[GameSchedule] = []

    _debug_print(debug, f"[NPB OFFICIAL] Parsed games: {len(games)}")
    return games


# ==========================
# PINNACLE API SCRAPER
# ==========================

def fetch_pinnacle_api_odds(league: str, target_date: dt.date, debug: bool = False) -> Dict[Tuple[str, str, str, dt.date], GameOdds]:
    url = PINNACLE_API_URL_TEMPLATE.format(
        league=league.lower(),
        date=target_date.strftime("%Y-%m-%d"),
    )
    _debug_print(debug, f"[PINNACLE API {league.upper()}] GET {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        _debug_print(debug, f"[PINNACLE API {league.upper()}] Error: {e}")
        return {}

    # TODO: parse Pinnacle API JSON
    data = resp.json()
    odds_map: Dict[Tuple[str, str, str, dt.date], GameOdds] = {}

    # Example stub structure:
    # for event in data.get("events", []):
    #     home = _normalize_pinnacle_team(event["home"])
    #     away = _normalize_pinnacle_team(event["away"])
    #     key = _game_key(league, home, away, target_date)
    #     odds_map[key] = GameOdds(
    #         league=league,
    #         date=target_date,
    #         home_team=home,
    #         away_team=away,
    #         moneyline_home=...,
    #         moneyline_away=...,
    #         total=...,
    #         total_over_price=...,
    #         total_under_price=...,
    #         runline_home=...,
    #         runline_home_price=...,
    #         runline_away=...,
    #         runline_away_price=...,
    #         source="pinnacle_api",
    #     )

    _debug_print(debug, f"[PINNACLE API {league.upper()}] Parsed odds: {len(odds_map)}")
    return odds_map


# ==========================
# PINNACLE WEB JSON SCRAPER
# ==========================

def fetch_pinnacle_web_odds(league: str, target_date: dt.date, debug: bool = False) -> Dict[Tuple[str, str, str, dt.date], GameOdds]:
    url = PINNACLE_WEB_JSON_URL_TEMPLATE.format(
        league=league.lower(),
        date=target_date.strftime("%Y-%m-%d"),
    )
    _debug_print(debug, f"[PINNACLE WEB {league.upper()}] GET {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        _debug_print(debug, f"[PINNACLE WEB {league.upper()}] Error: {e}")
        return {}

    # TODO: parse hidden JSON used by Pinnacle frontend
    data = resp.json()
    odds_map: Dict[Tuple[str, str, str, dt.date], GameOdds] = {}

    # Example stub structure:
    # for event in data.get("events", []):
    #     home = _normalize_pinnacle_team(event["home"])
    #     away = _normalize_pinnacle_team(event["away"])
    #     key = _game_key(league, home, away, target_date)
    #     odds_map[key] = GameOdds(
    #         league=league,
    #         date=target_date,
    #         home_team=home,
    #         away_team=away,
    #         moneyline_home=...,
    #         moneyline_away=...,
    #         total=...,
    #         total_over_price=...,
    #         total_under_price=...,
    #         runline_home=...,
    #         runline_home_price=...,
    #         runline_away=...,
    #         runline_away_price=...,
    #         source="pinnacle_web",
    #     )

    _debug_print(debug, f"[PINNACLE WEB {league.upper()}] Parsed odds: {len(odds_map)}")
    return odds_map


# ==========================
# MERGER
# ==========================

def merge_schedule_and_odds(
    league: str,
    schedule: List[GameSchedule],
    api_odds: Dict[Tuple[str, str, str, dt.date], GameOdds],
    web_odds: Dict[Tuple[str, str, str, dt.date], GameOdds],
    debug: bool = False,
) -> List[ProjectionGame]:
    merged: List[ProjectionGame] = []

    for game in schedule:
        home = _normalize_team(game.home_team, league)
        away = _normalize_team(game.away_team, league)
        key = _game_key(league, home, away, game.date)

        base_odds = api_odds.get(key)
        override_odds = web_odds.get(key)

        if override_odds:
            odds = override_odds
            _debug_print(debug, f"[MERGE {league.upper()}] Using WEB odds for {home} vs {away}")
        else:
            odds = base_odds
            if odds:
                _debug_print(debug, f"[MERGE {league.upper()}] Using API odds for {home} vs {away}")
            else:
                _debug_print(debug, f"[MERGE {league.upper()}] No odds for {home} vs {away}")

        pg = ProjectionGame(
            league=league,
            date=game.date,
            home_team=home,
            away_team=away,
            start_time=game.start_time,
            status=game.status,
            moneyline_home=odds.moneyline_home if odds else None,
            moneyline_away=odds.moneyline_away if odds else None,
            total=odds.total if odds else None,
            total_over_price=odds.total_over_price if odds else None,
            total_under_price=odds.total_under_price if odds else None,
            runline_home=odds.runline_home if odds else None,
            runline_home_price=odds.runline_home_price if odds else None,
            runline_away=odds.runline_away if odds else None,
            runline_away_price=odds.runline_away_price if odds else None,
        )
        merged.append(pg)

    _debug_print(debug, f"[MERGE {league.upper()}] Final merged games: {len(merged)}")
    return merged


# ==========================
# PUBLIC API FOR ROUTER
# ==========================

def get_projections(
    league: str,
    target_date: Optional[dt.date] = None,
    debug: bool = False,
) -> List[Dict]:
    """
    Public entrypoint for the global router.

    league: "kbo" or "npb"
    target_date: date object (defaults to today)
    """
    league = league.lower()
    date = target_date or dt.date.today()

    if league not in ("kbo", "npb"):
        raise ValueError(f"Unsupported league: {league}")

    if league == "kbo":
        schedule = fetch_kbo_official_schedule(date, debug=debug)
    else:
        schedule = fetch_npb_official_schedule(date, debug=debug)

    api_odds = fetch_pinnacle_api_odds(league, date, debug=debug)
    web_odds = fetch_pinnacle_web_odds(league, date, debug=debug)

    merged = merge_schedule_and_odds(
        league=league,
        schedule=schedule,
        api_odds=api_odds,
        web_odds=web_odds,
        debug=debug,
    )

    # Return as list of dicts for easy JSON/serialization
    return [asdict(g) for g in merged]


# ==========================
# DIAGNOSTIC CLI
# ==========================

def run_diagnostic(target_date: dt.date, debug: bool = False) -> None:
    print("==============================================")
    print("OVERSEAS ENGINE DIAGNOSTIC")
    print("==============================================")
    print(f"Date: {target_date.isoformat()}")
    print()

    for league in ("kbo", "npb"):
        print(f"► {league.upper()} OFFICIAL SCHEDULE")
        if league == "kbo":
            schedule = fetch_kbo_official_schedule(target_date, debug=debug)
        else:
            schedule = fetch_npb_official_schedule(target_date, debug=debug)

        print(f"Games found: {len(schedule)}")
        if schedule:
            sample = schedule[0]
            print("Sample:", {
                "home": sample.home_team,
                "away": sample.away_team,
                "start_time": sample.start_time,
                "status": sample.status,
            })
        else:
            print("Sample: []")
        print()

        print(f"► {league.upper()} PINNACLE API ODDS")
        api_odds = fetch_pinnacle_api_odds(league, target_date, debug=debug)
        print(f"Games with API odds: {len(api_odds)}")
        print()

        print(f"► {league.upper()} PINNACLE WEB ODDS")
        web_odds = fetch_pinnacle_web_odds(league, target_date, debug=debug)
        print(f"Games with WEB odds: {len(web_odds)}")
        print()

        print(f"► {league.upper()} MERGED PROJECTIONS")
        merged = merge_schedule_and_odds(
            league=league,
            schedule=schedule,
            api_odds=api_odds,
            web_odds=web_odds,
            debug=debug,
        )
        print(f"Games built: {len(merged)}")
        if merged:
            print("Sample:", asdict(merged[0]))
        else:
            print("Sample: []")
        print()

    print("==============================================")


def _cli():
    parser = argparse.ArgumentParser(description="Overseas Engine (KBO/NPB) – Official + Pinnacle")
    parser.add_argument(
        "--date",
        type=str,
        help="Target date in YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug logging",
    )
    parser.add_argument(
        "--league",
        type=str,
        choices=["kbo", "npb", "both"],
        default="both",
        help="League to run (default: both)",
    )

    args = parser.parse_args()
    target_date = _parse_date(args.date)

    if args.league == "both":
        run_diagnostic(target_date, debug=args.debug)
    else:
        # Single-league diagnostic using get_projections
        print("==============================================")
        print(f"OVERSEAS ENGINE DIAGNOSTIC – {args.league.upper()}")
        print("==============================================")
        print(f"Date: {target_date.isoformat()}")
        print()

        projections = get_projections(args.league, target_date=target_date, debug=args.debug)
        print(f"Games built: {len(projections)}")
        if projections:
            print("Sample:", projections[0])
        else:
            print("Sample: []")
        print("==============================================")


if __name__ == "__main__":
    _cli()
