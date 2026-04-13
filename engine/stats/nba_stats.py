import requests
import logging
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
NBA_API = "https://stats.nba.com/stats"
CURRENT_YEAR = datetime.now().year
LEAGUE_AVG_3PA = 12.0
LEAGUE_AVG_3P_PCT = 0.360
LEAGUE_AVG_PACE = 99.0
LEAGUE_AVG_DEF_RATING = 113.0
 
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Referer": "https://www.nba.com/",
    "Accept": "application/json",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
}
 
 
def get_season_str(year=None):
    y = year or CURRENT_YEAR
    return str(y - 1) + "-" + str(y)[2:]
 
 
def get_player_id(player_name):
    try:
        url = NBA_API + "/commonallplayers"
        params = {"LeagueID": "00", "Season": get_season_str(), "IsOnlyCurrentSeason": 1}
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        headers = data["resultSets"][0]["headers"]
        rows = data["resultSets"][0]["rowSet"]
        name_idx = headers.index("DISPLAY_FIRST_LAST")
        id_idx = headers.index("PERSON_ID")
        for row in rows:
            if player_name.lower() in row[name_idx].lower():
                logger.info("Found NBA player " + player_name + ": ID=" + str(row[id_idx]))
                return row[id_idx]
        logger.warning("NBA player not found: " + player_name)
        return None
    except Exception as e:
        logger.error("NBA player ID failed: " + str(e))
        return None
 
 
def get_player_season_stats(player_id, season_str=None):
    try:
        url = NBA_API + "/playerdashboardbyyearoveryear"
        params = {"PlayerID": player_id, "PerMode": "PerGame", "Season": season_str or get_season_str(), "SeasonType": "Regular Season", "LeagueID": "00"}
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        rows = data["resultSets"][0]["rowSet"]
        hdrs = data["resultSets"][0]["headers"]
        if not rows:
            return None
        row = rows[-1]
        def g(field):
            try:
                return row[hdrs.index(field)]
            except Exception:
                return 0
        return {
            "fg3a": float(g("FG3A") or 0),
            "fg3m": float(g("FG3M") or 0),
            "fg3_pct": float(g("FG3_PCT") or 0),
            "pts": float(g("PTS") or 0),
            "ast": float(g("AST") or 0),
            "reb": float(g("REB") or 0),
            "min": float(g("MIN") or 0),
            "games": int(g("GP") or 1),
        }
    except Exception as e:
        logger.error("NBA season stats failed for " + str(player_id) + ": " + str(e))
        return None
 
 
def get_player_last_n_games(player_id, n=10):
    try:
        url = NBA_API + "/playergamelog"
        params = {"PlayerID": player_id, "Season": get_season_str(), "SeasonType": "Regular Season", "LastNGames": n}
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        rows = data["resultSets"][0]["rowSet"]
        hdrs = data["resultSets"][0]["headers"]
        if not rows:
            return None
        games = []
        for row in rows[:n]:
            def g(field):
                try:
                    return row[hdrs.index(field)]
                except Exception:
                    return 0
            games.append({
                "fg3a": float(g("FG3A") or 0),
                "fg3m": float(g("FG3M") or 0),
                "pts": float(g("PTS") or 0),
                "ast": float(g("AST") or 0),
                "reb": float(g("REB") or 0),
                "min": float(g("MIN") or 0),
            })
        recent = games[:n]
        n_games = len(recent)
        avg_3pa = round(sum(g["fg3a"] for g in recent) / n_games, 2) if n_games > 0 else 0
        avg_3pm = round(sum(g["fg3m"] for g in recent) / n_games, 2) if n_games > 0 else 0
        avg_pts = round(sum(g["pts"] for g in recent) / n_games, 2) if n_games > 0 else 0
        avg_ast = round(sum(g["ast"] for g in recent) / n_games, 2) if n_games > 0 else 0
        avg_reb = round(sum(g["reb"] for g in recent) / n_games, 2) if n_games > 0 else 0
        avg_min = round(sum(g["min"] for g in recent) / n_games, 2) if n_games > 0 else 0
        return {"avg_3pa": avg_3pa, "avg_3pm": avg_3pm, "avg_pts": avg_pts, "avg_ast": avg_ast, "avg_reb": avg_reb, "avg_min": avg_min, "games_sampled": n_games}
    except Exception as e:
        logger.error("NBA last N games failed: " + str(e))
        return None
 
 
def get_team_pace(team_id):
    try:
        url = NBA_API + "/teamdashboardbygeneralsplits"
        params = {"TeamID": team_id, "Season": get_season_str(), "SeasonType": "Regular Season", "PerMode": "Per100Possessions"}
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        rows = data["resultSets"][0]["rowSet"]
        hdrs = data["resultSets"][0]["headers"]
        if not rows:
            return LEAGUE_AVG_PACE
        row = rows[0]
        try:
            pace = float(row[hdrs.index("PACE")] or LEAGUE_AVG_PACE)
        except Exception:
            pace = LEAGUE_AVG_PACE
        return pace
    except Exception as e:
        logger.error("Team pace failed: " + str(e))
        return LEAGUE_AVG_PACE
 
 
def get_opponent_3p_defense(team_id):
    try:
        url = NBA_API + "/leaguedashteamstats"
        params = {"Season": get_season_str(), "SeasonType": "Regular Season", "PerMode": "PerGame", "MeasureType": "Opponent"}
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        rows = data["resultSets"][0]["rowSet"]
        hdrs = data["resultSets"][0]["headers"]
        team_id_idx = hdrs.index("TEAM_ID")
        fg3a_idx = hdrs.index("OPP_FG3A")
        for row in rows:
            if row[team_id_idx] == team_id:
                opp_3pa = float(row[fg3a_idx] or LEAGUE_AVG_3PA)
                adj = round(opp_3pa / LEAGUE_AVG_3PA, 4)
                logger.info("Opp 3P defense: team=" + str(team_id) + " 3PA=" + str(opp_3pa) + " adj=" + str(adj))
                return opp_3pa, adj
        return LEAGUE_AVG_3PA, 1.0
    except Exception as e:
        logger.error("Opponent 3P defense failed: " + str(e))
        return LEAGUE_AVG_3PA, 1.0
 
 
def get_rest_days(player_id):
    try:
        url = NBA_API + "/playergamelog"
        params = {"PlayerID": player_id, "Season": get_season_str(), "SeasonType": "Regular Season", "LastNGames": 3}
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        rows = data["resultSets"][0]["rowSet"]
        hdrs = data["resultSets"][0]["headers"]
        if not rows:
            return 2
        last_game_date = rows[0][hdrs.index("GAME_DATE")]
        last_date = datetime.strptime(last_game_date, "%b %d, %Y")
        days_rest = (datetime.now() - last_date).days
        return max(0, days_rest - 1)
    except Exception as e:
        logger.error("Rest days failed: " + str(e))
        return 2
 
 
def get_full_nba_player_profile(player_name, opponent_team_id=None):
    logger.info("Building NBA profile for " + player_name)
    player_id = get_player_id(player_name)
    if not player_id:
        return _fallback_nba_profile(player_name)
    season = get_player_season_stats(player_id)
    recent = get_player_last_n_games(player_id, 10)
    rest = get_rest_days(player_id)
    opp_3pa, opp_adj = get_opponent_3p_defense(opponent_team_id) if opponent_team_id else (LEAGUE_AVG_3PA, 1.0)
    fg3a_season = season.get("fg3a", 8.0) if season else 8.0
    fg3a_recent = recent.get("avg_3pa", fg3a_season) if recent else fg3a_season
    fg3a_blended = round((fg3a_recent * 0.60) + (fg3a_season * 0.40), 2)
    fg3m_season = season.get("fg3m", 2.5) if season else 2.5
    fg3m_recent = recent.get("avg_3pm", fg3m_season) if recent else fg3m_season
    fg3m_blended = round((fg3m_recent * 0.60) + (fg3m_season * 0.40), 2)
    rest_adj = 1.0
    if rest == 0:
        rest_adj = 0.93
    elif rest == 1:
        rest_adj = 0.97
    elif rest >= 3:
        rest_adj = 1.03
    profile = {
        "player_name": player_name,
        "player_id": player_id,
        "fg3a_blended": fg3a_blended,
        "fg3m_blended": fg3m_blended,
        "fg3_pct": season.get("fg3_pct", 0.36) if season else 0.36,
        "pts_blended": round(((recent.get("avg_pts", 0) if recent else 0) * 0.60 + (season.get("pts", 0) if season else 0) * 0.40), 2),
        "ast_blended": round(((recent.get("avg_ast", 0) if recent else 0) * 0.60 + (season.get("ast", 0) if season else 0) * 0.40), 2),
        "reb_blended": round(((recent.get("avg_reb", 0) if recent else 0) * 0.60 + (season.get("reb", 0) if season else 0) * 0.40), 2),
        "min_blended": round(((recent.get("avg_min", 0) if recent else 0) * 0.60 + (season.get("min", 0) if season else 0) * 0.40), 2),
        "rest_days": rest,
        "rest_adj": rest_adj,
        "opp_3pa_allowed": opp_3pa,
        "opp_3p_adj": opp_adj,
        "attempts_per_game": fg3a_blended,
        "opp_defense_rate": opp_3pa,
    }
    logger.info("NBA profile: " + player_name + " 3PA=" + str(fg3a_blended) + " rest=" + str(rest) + " oppAdj=" + str(opp_adj))
    return profile
 
 
def _fallback_nba_profile(player_name):
    return {
        "player_name": player_name, "player_id": None,
        "fg3a_blended": 8.0, "fg3m_blended": 2.5, "fg3_pct": 0.36,
        "pts_blended": 18.0, "ast_blended": 4.0, "reb_blended": 4.0, "min_blended": 32.0,
        "rest_days": 2, "rest_adj": 1.0,
        "opp_3pa_allowed": LEAGUE_AVG_3PA, "opp_3p_adj": 1.0,
        "attempts_per_game": 8.0, "opp_defense_rate": LEAGUE_AVG_3PA,
    }
