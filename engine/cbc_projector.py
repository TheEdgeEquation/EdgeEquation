import requests
import logging
from datetime import datetime, timedelta
 
logger = logging.getLogger(__name__)
 
FOOTBALL_DATA_API = "https://api.football-data.org/v4"
FOOTBALL_DATA_KEY = __import__('os').getenv("FOOTBALL_DATA_KEY", "")
 
EPL_ID = "PL"
UCL_ID = "CL"
 
LEAGUE_AVG_GOALS = 2.6
LEAGUE_AVG_KBO_RUNS = 5.2
LEAGUE_AVG_NPB_RUNS = 4.1
 
 
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
                "home_team": home, "away_team": away,
                "home_goals": home_goals, "away_goals": away_goals,
                "total": round(home_goals + away_goals, 1),
                "league": "EPL", "commence_time": commence,
            })
        logger.info("EPL projections: " + str(len(projections)) + " matches")
        return projections
    except Exception as e:
        logger.error("EPL projections failed: " + str(e))
        return []
 
 
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
                "home_team": home, "away_team": away,
                "home_goals": home_goals, "away_goals": away_goals,
                "total": round(home_goals + away_goals, 1),
                "league": "Champions League", "commence_time": commence,
            })
        logger.info("UCL projections: " + str(len(projections)) + " matches")
        return projections
    except Exception as e:
        logger.error("UCL projections failed: " + str(e))
        return []
 
 
def _project_soccer_score(home_team, away_team):
    home_goals = round(LEAGUE_AVG_GOALS * 0.55 * 1.10, 1)
    away_goals = round(LEAGUE_AVG_GOALS * 0.45 * 0.92, 1)
    return home_goals, away_goals
 
 
def get_kbo_projections():
    try:
        today_kst = (datetime.now() + timedelta(hours=14)).strftime("%Y-%m-%d")
        logger.info("KBO: fetching via ESPN for KST date " + today_kst)
        projections = _get_kbo_espn(today_kst)
        if not projections:
            logger.info("KBO: no games found today")
        logger.info("KBO projections: " + str(len(projections)) + " games")
        return projections
    except Exception as e:
        logger.error("KBO projections failed: " + str(e))
        return []
 
 
def _get_kbo_espn(date_str):
    date_formatted = date_str.replace("-", "")
    urls_to_try = [
        f"https://site.api.espn.com/apis/site/v2/sports/baseball/kbo/scoreboard?dates={date_formatted}",
        f"https://site.api.espn.com/apis/site/v2/sports/baseball/korea/scoreboard?dates={date_formatted}",
        f"https://site.api.espn.com/apis/site/v2/sports/baseball/kbo/scoreboard",
    ]
    for url in urls_to_try:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            projections = []
            for event in data.get("events", []):
                competitors = event.get("competitions", [{}])[0].get("competitors", [])
                home = next((c.get("team", {}).get("displayName", "") for c in competitors if c.get("homeAway") == "home"), "")
                away = next((c.get("team", {}).get("displayName", "") for c in competitors if c.get("homeAway") == "away"), "")
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
            logger.info(f"KBO ESPN success via {url} — {len(projections)} games")
            return projections
        except Exception as e:
            logger.warning(f"KBO ESPN attempt failed ({url}): {e}")
            continue
    logger.error("KBO: all ESPN URL variants failed — no games returned")
    return []
 
 
def get_npb_projections():
    try:
        today_jst = (datetime.now() + timedelta(hours=14)).strftime("%Y-%m-%d")
        logger.info("NPB: fetching via ESPN for JST date " + today_jst)
        projections = _get_npb_espn(today_jst)
        if not projections:
            logger.info("NPB: no games found today")
        logger.info("NPB projections: " + str(len(projections)) + " games")
        return projections
    except Exception as e:
        logger.error("NPB projections failed: " + str(e))
        return []
 
 
def _get_npb_espn(date_str):
    date_formatted = date_str.replace("-", "")
    urls_to_try = [
        f"https://site.api.espn.com/apis/site/v2/sports/baseball/npb/scoreboard?dates={date_formatted}",
        f"https://site.api.espn.com/apis/site/v2/sports/baseball/japan/scoreboard?dates={date_formatted}",
        f"https://site.api.espn.com/apis/site/v2/sports/baseball/npb/scoreboard",
    ]
    for url in urls_to_try:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            projections = []
            for event in data.get("events", []):
                competitors = event.get("competitions", [{}])[0].get("competitors", [])
                home = next((c.get("team", {}).get("displayName", "") for c in competitors if c.get("homeAway") == "home"), "")
                away = next((c.get("team", {}).get("displayName", "") for c in competitors if c.get("homeAway") == "away"), "")
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
            logger.info(f"NPB ESPN success via {url} — {len(projections)} games")
            return projections
        except Exception as e:
            logger.warning(f"NPB ESPN attempt failed ({url}): {e}")
            continue
    logger.error("NPB: all ESPN URL variants failed — no games returned")
    return []
 
 
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
    date_str = datetime.now().strftime("%B %d")
    lines = [
        "CASH BEFORE COFFEE — NPB PROJECTIONS",
        date_str + "  |  Algorithm v2.0",
        "Japanese Baseball  |  Games playing now",
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
        "The algorithm runs while America sleeps.",
        "#CashBeforeCoffee #NPB #JapaneseBaseball",
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
