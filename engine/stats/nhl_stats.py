import requests
import logging
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
NHL_API = "https://api-web.nhle.com/v1"
NHL_STATS_API = "https://api.nhle.com/stats/rest/en"
CURRENT_YEAR = datetime.now().year
LEAGUE_AVG_SOG = 3.2
LEAGUE_AVG_SOG_PER_60 = 4.8
LEAGUE_AVG_TOI = 18.0
LEAGUE_AVG_SOG_ALLOWED = 30.5
 
 
def get_player_id(player_name):
    try:
        url = "https://search.d3.nhle.com/api/v1/search"
        params = {"q": player_name, "type": "player", "culture": "en-us", "limit": 5}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json()
        for r in results:
            if player_name.lower() in r.get("name", "").lower():
                pid = r.get("playerId") or r.get("id")
                logger.info("Found NHL player " + player_name + ": ID=" + str(pid))
                return pid
        return None
    except Exception as e:
        logger.error("NHL player ID failed: " + str(e))
        return None
 
 
def get_player_season_stats(player_id):
    try:
        url = NHL_API + "/player/" + str(player_id) + "/landing"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        season_stats = data.get("featuredStats", {}).get("regularSeason", {}).get("subSeason", {})
        career = data.get("careerTotals", {}).get("regularSeason", {})
        gp = season_stats.get("gamesPlayed", 1) or 1
        sog = season_stats.get("shots", 0) or 0
        goals = season_stats.get("goals", 0) or 0
        toi_str = season_stats.get("timeOnIcePerGame", "18:00") or "18:00"
        try:
            parts = toi_str.split(":")
            toi = int(parts[0]) + int(parts[1]) / 60
        except Exception:
            toi = LEAGUE_AVG_TOI
        sog_per_game = round(sog / gp, 2) if gp > 0 else 0
        goals_per_game = round(goals / gp, 2) if gp > 0 else 0
        sog_per_60 = round(sog_per_game / toi * 60, 2) if toi > 0 else LEAGUE_AVG_SOG_PER_60
        return {"sog_per_game": sog_per_game, "sog_per_60": sog_per_60, "goals_per_game": goals_per_game, "avg_toi": toi, "games_played": gp}
    except Exception as e:
        logger.error("NHL season stats failed for " + str(player_id) + ": " + str(e))
        return None
 
 
def get_player_last_n_games(player_id, n=10):
    try:
        url = NHL_API + "/player/" + str(player_id) + "/game-log/now"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        games = data.get("gameLog", [])[:n]
        if not games:
            return None
        total_sog = 0
        total_goals = 0
        total_toi = 0
        count = 0
        for game in games:
            sog = game.get("shots", 0) or 0
            goals = game.get("goals", 0) or 0
            toi_str = game.get("toi", "18:00") or "18:00"
            try:
                parts = toi_str.split(":")
                toi = int(parts[0]) + int(parts[1]) / 60
            except Exception:
                toi = LEAGUE_AVG_TOI
            total_sog += sog
            total_goals += goals
            total_toi += toi
            count += 1
        avg_sog = round(total_sog / count, 2) if count > 0 else 0
        avg_goals = round(total_goals / count, 2) if count > 0 else 0
        avg_toi = round(total_toi / count, 2) if count > 0 else LEAGUE_AVG_TOI
        sog_per_60 = round(avg_sog / avg_toi * 60, 2) if avg_toi > 0 else LEAGUE_AVG_SOG_PER_60
        return {"avg_sog": avg_sog, "avg_goals": avg_goals, "avg_toi": avg_toi, "sog_per_60": sog_per_60, "games_sampled": count}
    except Exception as e:
        logger.error("NHL last N games failed: " + str(e))
        return None
 
 
def get_opponent_sog_allowed(team_abbr):
    try:
        url = NHL_STATS_API + "/team"
        params = {"isAggregate": False, "isGame": False, "sort": '[{"property":"shotsAgainstPerGame","direction":"DESC"}]', "start": 0, "limit": 32, "factCayenneExp": "gamesPlayed>=1", "cayenneExp": 'gameTypeId=2 and seasonId>=' + str(CURRENT_YEAR-1) + str(CURRENT_YEAR)}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        for team in data.get("data", []):
            if team_abbr.upper() in team.get("teamAbbrev", "").upper():
                sog_allowed = float(team.get("shotsAgainstPerGame", LEAGUE_AVG_SOG_ALLOWED) or LEAGUE_AVG_SOG_ALLOWED)
                adj = round(sog_allowed / LEAGUE_AVG_SOG_ALLOWED, 4)
                logger.info("Opp SOG allowed: " + team_abbr + " = " + str(sog_allowed) + " adj=" + str(adj))
                return sog_allowed, adj
        return LEAGUE_AVG_SOG_ALLOWED, 1.0
    except Exception as e:
        logger.error("NHL opponent SOG failed: " + str(e))
        return LEAGUE_AVG_SOG_ALLOWED, 1.0
 
 
def get_full_nhl_player_profile(player_name, opponent_abbr=None):
    logger.info("Building NHL profile for " + player_name)
    player_id = get_player_id(player_name)
    if not player_id:
        return _fallback_nhl_profile(player_name)
    season = get_player_season_stats(player_id)
    recent = get_player_last_n_games(player_id, 10)
    opp_sog, opp_adj = get_opponent_sog_allowed(opponent_abbr) if opponent_abbr else (LEAGUE_AVG_SOG_ALLOWED, 1.0)
    sog_season = season.get("sog_per_game", LEAGUE_AVG_SOG) if season else LEAGUE_AVG_SOG
    sog_recent = recent.get("avg_sog", sog_season) if recent else sog_season
    sog_blended = round((sog_recent * 0.60) + (sog_season * 0.40), 2)
    sog60_season = season.get("sog_per_60", LEAGUE_AVG_SOG_PER_60) if season else LEAGUE_AVG_SOG_PER_60
    sog60_recent = recent.get("sog_per_60", sog60_season) if recent else sog60_season
    sog60_blended = round((sog60_recent * 0.60) + (sog60_season * 0.40), 2)
    toi_season = season.get("avg_toi", LEAGUE_AVG_TOI) if season else LEAGUE_AVG_TOI
    toi_recent = recent.get("avg_toi", toi_season) if recent else toi_season
    toi_blended = round((toi_recent * 0.60) + (toi_season * 0.40), 2)
    profile = {
        "player_name": player_name, "player_id": player_id,
        "sog_per_game": sog_blended, "sog_per_60": sog60_blended,
        "avg_toi": toi_blended,
        "goals_per_game": season.get("goals_per_game", 0.3) if season else 0.3,
        "opp_sog_allowed": opp_sog, "opp_sog_adj": opp_adj,
    }
    logger.info("NHL profile: " + player_name + " SOG=" + str(sog_blended) + " SOG/60=" + str(sog60_blended) + " TOI=" + str(toi_blended))
    return profile
 
 
def _fallback_nhl_profile(player_name):
    return {
        "player_name": player_name, "player_id": None,
        "sog_per_game": LEAGUE_AVG_SOG, "sog_per_60": LEAGUE_AVG_SOG_PER_60,
        "avg_toi": LEAGUE_AVG_TOI, "goals_per_game": 0.3,
        "opp_sog_allowed": LEAGUE_AVG_SOG_ALLOWED, "opp_sog_adj": 1.0,
    }
