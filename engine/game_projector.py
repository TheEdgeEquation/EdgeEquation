import requests
import logging
import math
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
MLB_API = "https://statsapi.mlb.com/api/v1"
NBA_API = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
NHL_API = "https://api-web.nhle.com/v1"
ESPN_MLB = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb"
 
LEAGUE_AVG_RUNS = 4.5
LEAGUE_AVG_NBA_SCORE = 113.0
LEAGUE_AVG_NHL_SCORE = 3.0
 
 
def get_mlb_game_projections():
    try:
        from engine.stats.mlb_stats import get_blended_pitcher_stats, get_pitcher_id
        from engine.stats.weather import get_weather
        from engine.stats.park_factors import get_park_factor, is_dome
 
        url = MLB_API + "/schedule"
        params = {"sportId": 1, "hydrate": "probablePitcher,team", "date": datetime.now().strftime("%Y-%m-%d")}
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        projections = []
 
        for date in data.get("dates", []):
            for game in date.get("games", []):
                try:
                    home = game.get("teams", {}).get("home", {})
                    away = game.get("teams", {}).get("away", {})
                    home_team = home.get("team", {}).get("name", "")
                    away_team = away.get("team", {}).get("name", "")
                    home_pitcher = home.get("probablePitcher", {}).get("fullName", "")
                    away_pitcher = away.get("probablePitcher", {}).get("fullName", "")
                    commence = game.get("gameDate", "")
 
                    home_runs = _project_team_runs(home_pitcher, away_team, home_team, True)
                    away_runs = _project_team_runs(away_pitcher, home_team, home_team, False)
 
                    weather = get_weather(home_team)
                    dome = is_dome(home_team)
                    if not dome:
                        wind = weather.get("wind_mph", 5)
                        temp = weather.get("temp_f", 70)
                        run_adj = 1.0
                        if wind > 15:
                            run_adj *= 1.04
                        if temp < 50:
                            run_adj *= 0.97
                        home_runs *= run_adj
                        away_runs *= run_adj
 
                    home_runs = round(home_runs, 1)
                    away_runs = round(away_runs, 1)
                    total = round(home_runs + away_runs, 1)
 
                    projections.append({
                        "home_team": home_team,
                        "away_team": away_team,
                        "home_pitcher": home_pitcher,
                        "away_pitcher": away_pitcher,
                        "home_runs": home_runs,
                        "away_runs": away_runs,
                        "total": total,
                        "commence_time": commence,
                        "weather": weather.get("condition", ""),
                        "dome": dome,
                    })
                except Exception as e:
                    logger.error("MLB game projection failed: " + str(e))
                    continue
 
        logger.info("MLB projections: " + str(len(projections)) + " games")
        return projections
 
    except Exception as e:
        logger.error("MLB projections failed: " + str(e))
        return []
 
 
def _project_team_runs(pitcher_name, batting_team, home_team, is_home):
    try:
        from engine.stats.mlb_stats import get_blended_pitcher_stats, get_pitcher_id, get_team_k_rate
        from engine.stats.park_factors import get_park_factor
 
        park = get_park_factor(home_team)
        park_run_factor = 2.0 - park.get("k_factor", 1.0)
 
        if pitcher_name:
            pid = get_pitcher_id(pitcher_name)
            if pid:
                stats = get_blended_pitcher_stats(pid)
                pitcher_era = stats.get("era", 4.25)
                avg_ip = min(stats.get("avg_innings_per_start", 5.5), 7.0)
            else:
                pitcher_era = 4.25
                avg_ip = 5.5
        else:
            pitcher_era = 4.25
            avg_ip = 5.5
 
        pitcher_runs = (pitcher_era / 9) * avg_ip
        bullpen_runs = (4.20 / 9) * (9 - avg_ip)
        total_runs = (pitcher_runs + bullpen_runs) * park_run_factor
        if is_home:
            total_runs *= 1.02
        return round(max(total_runs, 1.5), 1)
 
    except Exception as e:
        logger.error("Team runs projection failed: " + str(e))
        return LEAGUE_AVG_RUNS
 
 
def get_nba_game_projections():
    try:
        url = NBA_API + "/scoreboard"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        projections = []
 
        for event in data.get("events", []):
            try:
                competitors = event.get("competitions", [{}])[0].get("competitors", [])
                home = next((c for c in competitors if c.get("homeAway") == "home"), {})
                away = next((c for c in competitors if c.get("homeAway") == "away"), {})
                home_team = home.get("team", {}).get("displayName", "")
                away_team = away.get("team", {}).get("displayName", "")
                home_abbr = home.get("team", {}).get("abbreviation", "")
                away_abbr = away.get("team", {}).get("abbreviation", "")
                commence = event.get("date", "")
 
                home_score = _project_nba_score(home_abbr, away_abbr, True)
                away_score = _project_nba_score(away_abbr, home_abbr, False)
                total = round(home_score + away_score, 1)
 
                projections.append({
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_score": home_score,
                    "away_score": away_score,
                    "total": total,
                    "commence_time": commence,
                })
            except Exception as e:
                logger.error("NBA game projection failed: " + str(e))
                continue
 
        logger.info("NBA projections: " + str(len(projections)) + " games")
        return projections
 
    except Exception as e:
        logger.error("NBA projections failed: " + str(e))
        return []
 
 
def _project_nba_score(team_abbr, opp_abbr, is_home):
    base = LEAGUE_AVG_NBA_SCORE
    if is_home:
        base *= 1.015
    return round(base, 1)
 
 
def get_nhl_game_projections():
    try:
        url = NHL_API + "/schedule/now"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        projections = []
 
        games = data.get("gameWeek", [{}])[0].get("games", []) if data.get("gameWeek") else []
 
        for game in games:
            try:
                home_team = game.get("homeTeam", {}).get("placeName", {}).get("default", "")
                away_team = game.get("awayTeam", {}).get("placeName", {}).get("default", "")
                home_abbr = game.get("homeTeam", {}).get("abbrev", "")
                away_abbr = game.get("awayTeam", {}).get("abbrev", "")
                commence = game.get("startTimeUTC", "")
 
                home_goals = round(LEAGUE_AVG_NHL_SCORE * 1.02, 1)
                away_goals = round(LEAGUE_AVG_NHL_SCORE * 0.98, 1)
                total = round(home_goals + away_goals, 1)
 
                projections.append({
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_abbr": home_abbr,
                    "away_abbr": away_abbr,
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "total": total,
                    "commence_time": commence,
                })
            except Exception as e:
                logger.error("NHL game projection failed: " + str(e))
                continue
 
        logger.info("NHL projections: " + str(len(projections)) + " games")
        return projections
 
    except Exception as e:
        logger.error("NHL projections failed: " + str(e))
        return []
 
 
def get_mlb_pitcher_projections():
    try:
        from engine.prop_generator import get_mlb_starters
        from engine.stats.mlb_stats import get_full_pitcher_profile
        from engine.stats.savant import get_blended_savant_stats
 
        starters = get_mlb_starters()
        projections = []
 
        for starter in starters:
            try:
                player = starter["player"]
                home_team = starter["team"] if starter["home"] else starter["opponent"]
                profile = get_full_pitcher_profile(player, starter["opponent"], home_team)
                k9 = min(profile.get("k9_season", 8.0), 14.0)
                avg_ip = min(profile.get("avg_ip_recent", 5.5), 7.0)
                if avg_ip < 0.1:
                    avg_ip = 5.5
                base_k = round((k9 / 9.0) * avg_ip, 1)
                player_id = profile.get("player_id")
                swstr_pct = 0.107
                if player_id:
                    savant = get_blended_savant_stats(player_id)
                    swstr_pct = savant.get("swstr_pct", 0.107)
                projections.append({
                    "player": player,
                    "team": starter["team"],
                    "opponent": starter["opponent"],
                    "projected_ks": base_k,
                    "k9": round(k9, 1),
                    "avg_ip": avg_ip,
                    "swstr_pct": round(swstr_pct * 100, 1),
                    "home": starter["home"],
                })
            except Exception as e:
                logger.error("Pitcher projection failed for " + starter.get("player", "") + ": " + str(e))
 
        projections.sort(key=lambda x: -x["projected_ks"])
        logger.info("Pitcher projections: " + str(len(projections)))
        return projections
 
    except Exception as e:
        logger.error("Pitcher projections failed: " + str(e))
        return []
