import requests
import logging
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
MLB_API = "https://statsapi.mlb.com/api/v1"
NBA_API = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
NHL_API = "https://api-web.nhle.com/v1"
CURRENT_YEAR = datetime.now().year
MAX_IP_PER_START = 7.0
MAX_K9 = 14.0
 
TYPICAL_K_LINES = {
    (0, 4.0): {"line": 3.5, "over_odds": -115, "under_odds": -105},
    (4.0, 5.0): {"line": 4.5, "over_odds": -115, "under_odds": -105},
    (5.0, 6.0): {"line": 5.5, "over_odds": -115, "under_odds": -105},
    (6.0, 7.0): {"line": 6.5, "over_odds": -115, "under_odds": -105},
    (7.0, 8.0): {"line": 7.5, "over_odds": -115, "under_odds": -105},
    (8.0, 9.0): {"line": 8.5, "over_odds": -115, "under_odds": -105},
    (9.0, 10.0): {"line": 9.5, "over_odds": -115, "under_odds": -105},
    (10.0, 99.0): {"line": 10.5, "over_odds": -115, "under_odds": -105},
}
 
 
def american_to_implied(odds):
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)
 
 
def get_line_for_lambda(true_lambda, table=None):
    t = table or TYPICAL_K_LINES
    for (low, high), data in t.items():
        if low <= true_lambda < high:
            return data
    return {"line": round(true_lambda - 0.5, 1), "over_odds": -115, "under_odds": -105}
 
 
def get_mlb_starters():
    try:
        url = MLB_API + "/schedule"
        params = {"sportId": 1, "hydrate": "probablePitcher,team", "date": datetime.now().strftime("%Y-%m-%d")}
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        starters = []
        for date in data.get("dates", []):
            for game in date.get("games", []):
                home = game.get("teams", {}).get("home", {})
                away = game.get("teams", {}).get("away", {})
                home_team = home.get("team", {}).get("name", "")
                away_team = away.get("team", {}).get("name", "")
                home_pitcher = home.get("probablePitcher", {}).get("fullName", "")
                away_pitcher = away.get("probablePitcher", {}).get("fullName", "")
                commence = game.get("gameDate", "")
                if home_pitcher:
                    starters.append({"player": home_pitcher, "team": home_team, "opponent": away_team, "home": True, "commence_time": commence, "sport": "baseball_mlb", "sport_label": "MLB", "prop_label": "K", "icon": "⚾"})
                if away_pitcher:
                    starters.append({"player": away_pitcher, "team": away_team, "opponent": home_team, "home": False, "commence_time": commence, "sport": "baseball_mlb", "sport_label": "MLB", "prop_label": "K", "icon": "⚾"})
        logger.info("Found " + str(len(starters)) + " MLB starters")
        return starters
    except Exception as e:
        logger.error("MLB starters failed: " + str(e))
        return []
 
 
def get_nba_players():
    try:
        url = NBA_API + "/scoreboard"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        players = []
        for event in data.get("events", []):
            competitors = event.get("competitions", [{}])[0].get("competitors", [])
            home_team = next((c.get("team", {}).get("displayName", "") for c in competitors if c.get("homeAway") == "home"), "")
            away_team = next((c.get("team", {}).get("displayName", "") for c in competitors if c.get("homeAway") == "away"), "")
            commence = event.get("date", "")
            for comp in competitors:
                is_home = comp.get("homeAway") == "home"
                team = comp.get("team", {}).get("displayName", "")
                opponent = away_team if is_home else home_team
                roster = comp.get("roster", {}).get("entries", [])
                for player_entry in roster[:3]:
                    athlete = player_entry.get("athlete", {})
                    player_name = athlete.get("displayName", "")
                    position = athlete.get("position", {}).get("abbreviation", "G")
                    if player_name and position in ("G", "SF", "SG", "PG"):
                        players.append({"player": player_name, "team": team, "opponent": opponent, "home": is_home, "commence_time": commence, "sport": "basketball_nba", "sport_label": "NBA", "position": position})
        logger.info("Found " + str(len(players)) + " NBA players")
        return players
    except Exception as e:
        logger.error("NBA players failed: " + str(e))
        return []
 
 
def get_nhl_players():
    try:
        url = NHL_API + "/schedule/now"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        players = []
        for game in data.get("gameWeek", [{}])[0].get("games", []):
            home_team = game.get("homeTeam", {}).get("placeName", {}).get("default", "")
            away_team = game.get("awayTeam", {}).get("placeName", {}).get("default", "")
            home_abbr = game.get("homeTeam", {}).get("abbrev", "")
            away_abbr = game.get("awayTeam", {}).get("abbrev", "")
            commence = game.get("startTimeUTC", "")
            players.append({"player": "TBD", "team": home_team, "opponent": away_team, "home": True, "home_abbr": home_abbr, "away_abbr": away_abbr, "commence_time": commence, "sport": "icehockey_nhl", "sport_label": "NHL"})
        logger.info("Found " + str(len(players)) + " NHL games")
        return players
    except Exception as e:
        logger.error("NHL players failed: " + str(e))
        return []
 
 
def generate_k_props():
    from engine.stats.mlb_stats import get_full_pitcher_profile
    from engine.stats.weather import get_weather
    from engine.stats.umpire import get_umpire_for_game
    from engine.stats.park_factors import get_k_factor, get_altitude_adjustment
    from engine.stats.savant import get_blended_savant_stats, get_swstr_k_adjustment, get_pitch_mix_adjustment
 
    starters = get_mlb_starters()
    if not starters:
        return []
    props = []
    for starter in starters:
        try:
            player = starter["player"]
            home_team = starter["team"] if starter["home"] else starter["opponent"]
            away_team = starter["opponent"] if starter["home"] else starter["team"]
            profile = get_full_pitcher_profile(player, starter["opponent"], home_team)
            k9_season = min(profile.get("k9_season", 8.0), MAX_K9)
            k9_recent = min(profile.get("k9_recent", k9_season), MAX_K9)
            avg_ip = min(profile.get("avg_ip_recent", 5.5), MAX_IP_PER_START)
            if avg_ip < 0.1:
                avg_ip = 5.5
            k9_blended = min((k9_recent * 0.60) + (k9_season * 0.40), MAX_K9)
            base_lambda = (k9_blended / 9.0) * avg_ip
            base_lambda = min(base_lambda, 12.0)
            opp_adj = profile.get("opp_k_adjustment", 1.0)
            platoon_adj = profile.get("platoon_adjustment", 1.0)
            weather = get_weather(home_team)
            weather_adj = weather.get("k_adjustment", 1.0)
            umpire_name, umpire_adj = get_umpire_for_game(home_team, away_team)
            park_adj = get_k_factor(home_team)
            alt_adj = get_altitude_adjustment(home_team)
            player_id = profile.get("player_id")
            swstr_adj = 1.0
            pitch_mix_adj = 1.0
            swstr_pct = 0.107
            if player_id:
                savant = get_blended_savant_stats(player_id)
                swstr_pct = savant.get("swstr_pct", 0.107)
                swstr_adj = get_swstr_k_adjustment(swstr_pct)
                pitch_mix_adj = get_pitch_mix_adjustment(savant.get("breaking_ball_pct", 0.28))
            true_lambda = base_lambda * opp_adj * platoon_adj * weather_adj * umpire_adj * park_adj * alt_adj * swstr_adj * pitch_mix_adj
            true_lambda = min(round(true_lambda, 3), 12.0)
            line_data = get_line_for_lambda(true_lambda)
            line = line_data["line"]
            over_odds = line_data["over_odds"]
            under_odds = line_data["under_odds"]
            implied = american_to_implied(over_odds)
            logger.info(player + ": K9=" + str(round(k9_blended,2)) + " IP=" + str(avg_ip) + " lambda=" + str(true_lambda) + " line=" + str(line))
            props.append({
                **starter,
                "line": line, "over_odds": over_odds, "under_odds": under_odds,
                "implied_prob": round(implied, 4), "true_lambda": true_lambda,
                "source": "model_generated",
                "opp_k_adjustment": opp_adj, "platoon_adjustment": platoon_adj,
                "weather_adj": weather_adj, "umpire_adjustment": umpire_adj,
                "park_adj": park_adj, "swstr_pct": swstr_pct,
                "k9_season": k9_season, "opp_k_pct": profile.get("opp_k_pct", 0.225),
                "home_team": home_team,
            })
        except Exception as e:
            logger.error("K prop failed for " + starter.get("player", "") + ": " + str(e))
    logger.info("Generated " + str(len(props)) + " MLB K props")
    return props
 
 
def generate_nba_props():
    try:
        from engine.stats.nba_stats import get_full_nba_player_profile
        from engine.stats.nba_model import generate_nba_props as model_generate
        players = get_nba_players()
        if not players:
            return []
        players_with_profiles = []
        for p in players[:20]:
            try:
                profile = get_full_nba_player_profile(p["player"])
                players_with_profiles.append({**p, "player_name": p["player"], "profile": profile})
            except Exception as e:
                logger.error("NBA profile failed: " + str(e))
        return model_generate(players_with_profiles)
    except Exception as e:
        logger.error("NBA props failed: " + str(e))
        return []
 
 
def generate_nhl_props():
    try:
        from engine.stats.nhl_stats import get_full_nhl_player_profile
        from engine.stats.nhl_model import generate_nhl_props as model_generate
        games = get_nhl_players()
        if not games:
            return []
        players_with_profiles = []
        for game in games[:5]:
            try:
                away_abbr = game.get("away_abbr", "")
                profile = get_full_nhl_player_profile("TBD", away_abbr)
                players_with_profiles.append({**game, "player_name": "TBD", "profile": profile})
            except Exception as e:
                logger.error("NHL profile failed: " + str(e))
        return model_generate(players_with_profiles)
    except Exception as e:
        logger.error("NHL props failed: " + str(e))
        return []
 
 
def generate_all_props():
    all_props = []
    logger.info("Generating MLB K props...")
    mlb = generate_k_props()
    all_props.extend(mlb)
    logger.info("MLB: " + str(len(mlb)) + " props")
    logger.info("Generating NBA props...")
    try:
        nba = generate_nba_props()
        all_props.extend(nba)
        logger.info("NBA: " + str(len(nba)) + " props")
    except Exception as e:
        logger.error("NBA props skipped: " + str(e))
    logger.info("Generating NHL props...")
    try:
        nhl = generate_nhl_props()
        all_props.extend(nhl)
        logger.info("NHL: " + str(len(nhl)) + " props")
    except Exception as e:
        logger.error("NHL props skipped: " + str(e))
    logger.info("Total props generated: " + str(len(all_props)))
    return all_props
