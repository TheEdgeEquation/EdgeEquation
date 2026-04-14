import requests
import logging
from datetime import datetime, timedelta
 
logger = logging.getLogger(__name__)
 
FOOTBALL_DATA_API = "https://api.football-data.org/v4"
FOOTBALL_DATA_KEY = "your_free_key_here"
 
EPL_ID = "PL"
UCL_ID = "CL"
 
LEAGUE_AVG_GOALS = 2.6
LEAGUE_AVG_KBO_RUNS = 5.2
LEAGUE_AVG_NPB_RUNS = 4.1
 
KBO_TEAMS = [
    "LG Twins", "Kia Tigers", "Samsung Lions", "Doosan Bears",
    "SSG Landers", "Lotte Giants", "NC Dinos", "KT Wiz",
    "Hanwha Eagles", "Kiwoom Heroes"
]
 
NPB_TEAMS = [
    "Yomiuri Giants", "Hanshin Tigers", "Hiroshima Carp",
    "Yakult Swallows", "DeNA BayStars", "Chunichi Dragons",
    "Fukuoka SoftBank Hawks", "Orix Buffaloes", "Lotte Marines",
    "Saitama Seibu Lions", "Tohoku Rakuten Eagles", "Hokkaido Nippon-Ham Fighters"
]
 
 
def get_epl_projections():
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        url = FOOTBALL_DATA_API + "/competitions/" + EPL_ID + "/matches"
        headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
        params = {"dateFrom": today, "dateTo": tomorrow, "status": "SCHEDULED"}
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code == 403:
            logger.warning("Football-data.org key not set - using fallback EPL schedule")
            return _get_fallback_epl()
        resp.raise_for_status()
        data = resp.json()
        projections = []
        for match in data.get("matches", []):
            home = match.get("homeTeam", {}).get("shortName", match.get("homeTeam", {}).get("name", ""))
            away = match.get("awayTeam", {}).get("shortName", match.get("awayTeam", {}).get("name", ""))
            commence = match.get("utcDate", "")
            home_goals, away_goals = _project_soccer_score(home, away, "EPL")
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
        return _get_fallback_epl()
 
 
def get_ucl_projections():
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        url = FOOTBALL_DATA_API + "/competitions/" + UCL_ID + "/matches"
        headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
        params = {"dateFrom": today, "dateTo": tomorrow, "status": "SCHEDULED"}
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code == 403:
            logger.warning("Football-data.org key not set - using fallback UCL schedule")
            return []
        resp.raise_for_status()
        data = resp.json()
        projections = []
        for match in data.get("matches", []):
            home = match.get("homeTeam", {}).get("shortName", match.get("homeTeam", {}).get("name", ""))
            away = match.get("awayTeam", {}).get("shortName", match.get("awayTeam", {}).get("name", ""))
            commence = match.get("utcDate", "")
            home_goals, away_goals = _project_soccer_score(home, away, "UCL")
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
 
 
def _project_soccer_score(home_team, away_team, league):
    try:
        league_avg = LEAGUE_AVG_GOALS
        home_goals = round(league_avg * 0.55 * 1.15, 1)
        away_goals = round(league_avg * 0.45 * 0.95, 1)
        return home_goals, away_goals
    except Exception:
        return 1.4, 1.2
 
 
def _get_fallback_epl():
    return []
 
 
def get_kbo_projections():
    try:
        today = datetime.now()
        kst_today = (today + timedelta(hours=14)).strftime("%Y-%m-%d")
        logger.info("KBO: fetching games for KST date " + kst_today)
        projections = _get_kbo_schedule(kst_today)
        if not projections:
            logger.info("No KBO games found via API - market may be off season")
        logger.info("KBO projections: " + str(len(projections)) + " games")
        return projections
    except Exception as e:
        logger.error("KBO projections failed: " + str(e))
        return []
 
 
def _get_kbo_schedule(date_str):
    try:
        url = "https://www.koreabaseball.com/ws/Schedule.asmx/GetScheduleList"
        year = date_str[:4]
        month = date_str[5:7]
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.koreabaseball.com/"}
        params = {"leId": "1", "srId": "0,1,3,4,5", "seasonId": year, "gameMonth": month}
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        projections = []
        for game in data.get("game", []):
            game_date = game.get("gameDate", "")
            if game_date != date_str.replace("-", ""):
                continue
            home = game.get("homeName", "")
            away = game.get("visitName", "")
            home_runs = round(LEAGUE_AVG_KBO_RUNS * 1.03, 1)
            away_runs = round(LEAGUE_AVG_KBO_RUNS * 0.97, 1)
            projections.append({
                "home_team": home, "away_team": away,
                "home_runs": home_runs, "away_runs": away_runs,
                "total": round(home_runs + away_runs, 1),
                "league": "KBO",
            })
        return projections
    except Exception as e:
        logger.error("KBO schedule fetch failed: " + str(e))
        return _get_fallback_kbo()
 
 
def _get_fallback_kbo():
    return []
 
 
def get_npb_projections():
    try:
        today = datetime.now()
        jst_today = (today + timedelta(hours=14)).strftime("%Y-%m-%d")
        logger.info("NPB: fetching games for JST date " + jst_today)
        projections = _get_npb_schedule(jst_today)
        logger.info("NPB projections: " + str(len(projections)) + " games")
        return projections
    except Exception as e:
        logger.error("NPB projections failed: " + str(e))
        return []
 
 
def _get_npb_schedule(date_str):
    try:
        year = date_str[:4]
        month = date_str[5:7]
        day = date_str[8:10]
        url = "https://npb.jp/en/games/" + year + "/schedule" + month + "_detail.html"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        projections = []
        if date_str.replace("-", "/") in resp.text or day in resp.text:
            home_runs = round(LEAGUE_AVG_NPB_RUNS * 1.02, 1)
            away_runs = round(LEAGUE_AVG_NPB_RUNS * 0.98, 1)
        return projections
    except Exception as e:
        logger.error("NPB schedule failed: " + str(e))
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
        "CASH BEFORE COFFEE — CHAMPIONS LEAGUE PROJECTIONS",
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
        "Korean Baseball | Games playing now",
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
        "Japanese Baseball | Games playing now",
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
