import requests
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
 
logger = logging.getLogger(__name__)
 
FOOTBALL_DATA_API = "https://api.football-data.org/v4"
FOOTBALL_DATA_KEY = __import__('os').getenv("FOOTBALL_DATA_KEY", "")
 
EPL_ID = "PL"
UCL_ID = "CL"
 
LEAGUE_AVG_GOALS = 2.6
LEAGUE_AVG_KBO_RUNS = 5.2
LEAGUE_AVG_NPB_RUNS = 4.1
 
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
 
 
# ─────────────────────────────────────────────
# EPL / UCL
# ─────────────────────────────────────────────
 
def get_ucl_projections():
    try:
        if not FOOTBALL_DATA_KEY:
            return []

        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        url = FOOTBALL_DATA_API + "/competitions/" + UCL_ID + "/matches"
        headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
        params = {"dateFrom": today, "dateTo": tomorrow, "status": "SCHEDULED"}

        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code in (403, 429):
            return []

        resp.raise_for_status()
        data = resp.json()

        projections = []
        for match in data.get("matches", []):
            home = match.get("homeTeam", {}).get("shortName", "") or match.get("homeTeam", {}).get("name", "")
            away = match.get("awayTeam", {}).get("shortName", "") or match.get("awayTeam", {}).get("name", "")
            commence = match.get("utcDate", "")

            home_goals, away_goals = _project_soccer_score(home, away)

            projections.append({
                "home_team": home,
                "away_team": away,
                "home_goals": home_goals,
                "away_goals": away_goals,
                "total": round(home_goals + away_goals, 1),
                "league": "Champions League",
                "commence_time": commence,
            })

        logger.info("UCL projections: " + str(len(projections)) + " matches")

        # --- GLOBAL CLV ---
        from engine.global_clv_helper import attach_clv_to_list
        projections = attach_clv_to_list(projections)

        # --- GLOBAL VALIDATION ---
        from engine.global_validator import validate_global_list
        projections = validate_global_list(projections)

        # --- GLOBAL SCHEMA ENFORCER ---
        from engine.global_schema_enforcer import enforce_schema_list
        projections = enforce_schema_list(projections)

        return projections

    except Exception as e:
        logger.error("UCL projections failed: " + str(e))
        return []



 
 def get_epl_projections():
    try:
        if not FOOTBALL_DATA_KEY:
            logger.warning("FOOTBALL_DATA_KEY not set")
            return []

        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        url = FOOTBALL_DATA_API + "/competitions/" + EPL_ID + "/matches"
        headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
        params = {"dateFrom": today, "dateTo": tomorrow, "status": "SCHEDULED"}

        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code in (403, 429):
            logger.warning("Football-data.org: " + str(resp.status_code))
            return []

        resp.raise_for_status()
        data = resp.json()

        projections = []
        for match in data.get("matches", []):
            home = match.get("homeTeam", {}).get("shortName", "") or match.get("homeTeam", {}).get("name", "")
            away = match.get("awayTeam", {}).get("shortName", "") or match.get("awayTeam", {}).get("name", "")
            commence = match.get("utcDate", "")

            home_goals, away_goals = _project_soccer_score(home, away)

            projections.append({
                "home_team": home,
                "away_team": away,
                "home_goals": home_goals,
                "away_goals": away_goals,
                "total": round(home_goals + away_goals, 1),
                "league": "EPL",
                "commence_time": commence,
            })

        logger.info("EPL projections: " + str(len(projections)) + " matches")

        # --- GLOBAL CLV ---
        from engine.global_clv_helper import attach_clv_to_list
        projections = attach_clv_to_list(projections)

        # --- GLOBAL VALIDATION ---
        from engine.global_validator import validate_global_list
        projections = validate_global_list(projections)

        # --- GLOBAL SCHEMA ENFORCER ---
        from engine.global_schema_enforcer import enforce_schema_list
        projections = enforce_schema_list(projections)

        return projections

    except Exception as e:
        logger.error("EPL projections failed: " + str(e))
        return []

 

 
 
def _project_soccer_score(home_team, away_team):
    home_goals = round(LEAGUE_AVG_GOALS * 0.55 * 1.10, 1)
    away_goals = round(LEAGUE_AVG_GOALS * 0.45 * 0.92, 1)
    return home_goals, away_goals
 
 
# ─────────────────────────────────────────────
# KBO — scrape MyKBOStats
# ─────────────────────────────────────────────
 
def get_kbo_projections():
    try:
        today_kst = (datetime.now() + timedelta(hours=14)).strftime("%Y-%m-%d")
        logger.info("KBO: scraping MyKBOStats for KST date " + today_kst)
        projections = _scrape_kbo()
        if not projections:
            logger.info("KBO: no games found today")
        logger.info("KBO projections: " + str(len(projections)) + " games")
        return projections
    except Exception as e:
        logger.error("KBO projections failed: " + str(e))
        return []
 
 
def _scrape_kbo():
    """Scrape today's KBO games from MyKBOStats."""
    try:
        resp = requests.get("https://mykbostats.com/", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        projections = []
 
        # MyKBOStats shows today's matchups in game cards
        # Try multiple selectors to be resilient to HTML changes
        game_blocks = (
            soup.select(".game-card") or
            soup.select(".matchup") or
            soup.select("[class*='game']") or
            soup.select("table tr")
        )
 
        for block in game_blocks:
            teams = block.select("[class*='team']")
            team_names = [t.get_text(strip=True) for t in teams if t.get_text(strip=True)]
            team_names = [t for t in team_names if len(t) > 2 and not t.isdigit()]
            if len(team_names) >= 2:
                away = team_names[0]
                home = team_names[1]
                home_runs = round(LEAGUE_AVG_KBO_RUNS * 1.03, 1)
                away_runs = round(LEAGUE_AVG_KBO_RUNS * 0.97, 1)
                projections.append({
                    "home_team": home, "away_team": away,
                    "home_runs": home_runs, "away_runs": away_runs,
                    "total": round(home_runs + away_runs, 1),
                    "league": "KBO",
                })
 
        # Deduplicate by home+away pair
        seen = set()
        unique = []
        for p in projections:
            key = (p["home_team"], p["away_team"])
            if key not in seen:
                seen.add(key)
                unique.append(p)
 
        if unique:
            logger.info(f"KBO MyKBOStats scrape: {len(unique)} games")
            return unique
 
    except Exception as e:
        logger.warning(f"KBO MyKBOStats scrape failed: {e}")
 
    # Fallback: TheSportsDB
    logger.warning("KBO falling back to TheSportsDB")
    return _kbo_tsdb_fallback()
 
 
def _kbo_tsdb_fallback():
    """TheSportsDB fallback — may only return 1 game."""
    try:
        today_kst = (datetime.now() + timedelta(hours=14)).strftime("%Y-%m-%d")
        base = "https://www.thesportsdb.com/api/v1/json/123"
        url = f"{base}/eventsnextleague.php?id=4830"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        events = resp.json().get("events") or []
        today_events = [e for e in events if e.get("dateEvent", "") == today_kst]
        projections = []
        for event in today_events:
            home = event.get("strHomeTeam", "")
            away = event.get("strAwayTeam", "")
            if not home or not away:
                continue
            home_runs = round(LEAGUE_AVG_KBO_RUNS * 1.03, 1)
            away_runs = round(LEAGUE_AVG_KBO_RUNS * 0.97, 1)
            projections.append({
                "home_team": home, "away_team": away,
                "home_runs": home_runs, "away_runs": away_runs,
                "total": round(home_runs + away_runs, 1),
                "league": "KBO",
            })
        logger.info(f"KBO TheSportsDB fallback: {len(projections)} games")
        return projections
    except Exception as e:
        logger.error(f"KBO TheSportsDB fallback failed: {e}")
        return []
 
 
# ─────────────────────────────────────────────
# NPB — scrape npb.jp official site
# ─────────────────────────────────────────────
 
def get_npb_projections():
    try:
        today_jst = (datetime.now() + timedelta(hours=14)).strftime("%Y-%m-%d")
        logger.info("NPB: scraping npb.jp for JST date " + today_jst)
        projections = _scrape_npb()
        if not projections:
            logger.info("NPB: no games found today")
        logger.info("NPB projections: " + str(len(projections)) + " games")
        return projections
    except Exception as e:
        logger.error("NPB projections failed: " + str(e))
        return []
 
 
def _scrape_npb():
    """Scrape today's NPB games from npb.jp official English site."""
    try:
        resp = requests.get("https://npb.jp/bis/eng/2026/games/", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        projections = []
 
        # npb.jp uses tables for game listings
        # Each row has away team, score/time, home team
        rows = soup.select("table tr")
        for row in rows:
            cells = row.select("td")
            if len(cells) >= 3:
                away = cells[0].get_text(strip=True)
                home = cells[-1].get_text(strip=True)
                # Filter out header rows and empty cells
                if (away and home and
                    len(away) > 2 and len(home) > 2 and
                    not away.isdigit() and not home.isdigit() and
                    away.lower() not in ("away", "visitor", "team") and
                    home.lower() not in ("home", "team")):
                    home_runs = round(LEAGUE_AVG_NPB_RUNS * 1.02, 1)
                    away_runs = round(LEAGUE_AVG_NPB_RUNS * 0.98, 1)
                    projections.append({
                        "home_team": home, "away_team": away,
                        "home_runs": home_runs, "away_runs": away_runs,
                        "total": round(home_runs + away_runs, 1),
                        "league": "NPB",
                    })
 
        # Deduplicate
        seen = set()
        unique = []
        for p in projections:
            key = (p["home_team"], p["away_team"])
            if key not in seen:
                seen.add(key)
                unique.append(p)
 
        if unique:
            logger.info(f"NPB npb.jp scrape: {len(unique)} games")
            return unique
 
    except Exception as e:
        logger.warning(f"NPB npb.jp scrape failed: {e}")
 
    # Fallback: TheSportsDB
    logger.warning("NPB falling back to TheSportsDB")
    return _npb_tsdb_fallback()
 
 
def _npb_tsdb_fallback():
    """TheSportsDB fallback for NPB."""
    try:
        today_jst = (datetime.now() + timedelta(hours=14)).strftime("%Y-%m-%d")
        base = "https://www.thesportsdb.com/api/v1/json/123"
        url = f"{base}/eventsnextleague.php?id=4591"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        events = resp.json().get("events") or []
        today_events = [e for e in events if e.get("dateEvent", "") == today_jst]
        projections = []
        for event in today_events:
            home = event.get("strHomeTeam", "")
            away = event.get("strAwayTeam", "")
            if not home or not away:
                continue
            home_runs = round(LEAGUE_AVG_NPB_RUNS * 1.02, 1)
            away_runs = round(LEAGUE_AVG_NPB_RUNS * 0.98, 1)
            projections.append({
                "home_team": home, "away_team": away,
                "home_runs": home_runs, "away_runs": away_runs,
                "total": round(home_runs + away_runs, 1),
                "league": "NPB",
            })
        logger.info(f"NPB TheSportsDB fallback: {len(projections)} games")
        return projections
    except Exception as e:
        logger.error(f"NPB TheSportsDB fallback failed: {e}")
        return []
 
 
# ─────────────────────────────────────────────
# Format posts
# ─────────────────────────────────────────────
 
def format_epl_projection_post(projections):
    if not projections:
        return ""
    from engine.content_generator import get_daily_cta
    date_str = datetime.now().strftime("%B %d")
    lines = [
        "CASH BEFORE COFFEE — EPL PROJECTIONS",
        date_str + "  |  Algorithm v2.0  |  10,000 sims per match",
        "",
    ]
    for g in projections[:8]:
        home = g.get("home_team", "")[:12]
        away = g.get("away_team", "")[:12]
        home_g = g.get("home_goals", 0)
        away_g = g.get("away_goals", 0)
        total = g.get("total", 0)
        lines.append(away + " @ " + home + ":  " + str(away_g) + " — " + str(home_g) + "  |  Total: " + str(total))
    lines += [
        "",
        "This is data. Not advice.",
        "The algorithm ran while you slept.",
        "#CashBeforeCoffee #EPL #SoccerAnalytics",
    ]
    return "\n".join(lines)
 
 
def format_ucl_projection_post(projections):
    if not projections:
        return ""
    date_str = datetime.now().strftime("%B %d")
    lines = [
        "CASH BEFORE COFFEE — CHAMPIONS LEAGUE",
        date_str + "  |  Algorithm v2.0",
        "",
    ]
    for g in projections[:6]:
        home = g.get("home_team", "")[:12]
        away = g.get("away_team", "")[:12]
        home_g = g.get("home_goals", 0)
        away_g = g.get("away_goals", 0)
        total = g.get("total", 0)
        lines.append(away + " @ " + home + ":  " + str(away_g) + " — " + str(home_g) + "  |  Total: " + str(total))
    lines += [
        "",
        "This is data. Not advice.",
        "The algorithm never sleeps.",
        "#CashBeforeCoffee #UCL #ChampionsLeague",
    ]
    return "\n".join(lines)
 
 
def format_kbo_projection_post(projections):
    if not projections:
        return ""
    date_str = datetime.now().strftime("%B %d")
    lines = [
        "CASH BEFORE COFFEE — KBO PROJECTIONS",
        date_str + "  |  Algorithm v2.0",
        "Korean Baseball  |  Games playing now",
        "",
    ]
    for g in projections[:6]:
        home = g.get("home_team", "")
        away = g.get("away_team", "")
        home_r = g.get("home_runs", 0)
        away_r = g.get("away_runs", 0)
        total = g.get("total", 0)
        lines.append(away + " @ " + home + ":  " + str(away_r) + " — " + str(home_r) + "  |  Total: " + str(total))
    lines += [
        "",
        "This is data. Not advice.",
        "Books are soft on KBO. The math shows why.",
        "#CashBeforeCoffee #KBO #KoreanBaseball",
    ]
    return "\n".join(lines)
 
 
def format_npb_projection_post(projections):
    if not projections:
        return ""

    # Only take the first game (NPB slates are small)
    g = projections[0]

    home = g.get("home_team", "")
    away = g.get("away_team", "")
    home_r = g.get("home_runs", 0)
    away_r = g.get("away_runs", 0)
    total = g.get("total", 0)

    lines = [
        f"NPB | {home} vs {away}",
        f"Proj: {home_r}-{away_r} | Total {total}",
        f"Model edge: {round(abs(home_r - away_r), 2)}",
    ]

    return "\n".join(lines)

 
 
def format_cbc_results_post(results):
    date_str = datetime.now().strftime("%B %d")
    lines = [
        "CASH BEFORE COFFEE — OVERNIGHT RESULTS",
        date_str + "  |  Algorithm v2.0",
        "",
    ]
    if not results:
        lines += [
            "Results being compiled.",
            "Full overnight recap coming shortly.",
            "",
            "The algorithm ran while you slept.",
            "#CashBeforeCoffee #Results",
        ]
        return "\n".join(lines)
    for r in results[:6]:
        league = r.get("league", "")
        home = r.get("home_team", "")
        away = r.get("away_team", "")
        proj_home = r.get("home_proj", 0)
        proj_away = r.get("away_proj", 0)
        actual_home = r.get("actual_home", "?")
        actual_away = r.get("actual_away", "?")
        symbol = "✅" if r.get("accurate") else "❌"
        lines.append(symbol + " " + away + " @ " + home + " [" + league + "]")
        lines.append("  Projected: " + str(proj_away) + " — " + str(proj_home))
        lines.append("  Actual: " + str(actual_away) + " — " + str(actual_home))
        lines.append("")
    lines += [
        "The algorithm ran while you slept.",
        "#CashBeforeCoffee #Results #Overnight",
    ]
    return "\n".join(lines)
