import requests
import logging
from datetime import datetime, timedelta
 
logger = logging.getLogger(__name__)
MLB_API = "https://statsapi.mlb.com/api/v1"
CURRENT_YEAR = datetime.now().year
LAST_YEAR = CURRENT_YEAR - 1
LEAGUE_AVG_K_PCT = 0.225
LEAGUE_AVG_ERA = 4.25
 
 
def _today_str():
    return datetime.now().strftime("%Y-%m-%d")
 
 
def get_season_weight(current_starts):
    if current_starts <= 3:
        return 0.20, 0.80
    elif current_starts <= 6:
        return 0.40, 0.60
    elif current_starts <= 10:
        return 0.60, 0.40
    elif current_starts <= 15:
        return 0.75, 0.25
    else:
        return 0.90, 0.10
 
 
def get_pitcher_id(player_name):
    try:
        url = MLB_API + "/people/search"
        params = {"names": player_name, "sportId": 1}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        people = resp.json().get("people", [])
        if people:
            pid = people[0]["id"]
            logger.info("Found " + player_name + ": ID=" + str(pid))
            return pid
        logger.warning("Player not found: " + player_name)
        return None
    except Exception as e:
        logger.error("Player lookup failed for " + player_name + ": " + str(e))
        return None
 
 
def get_pitcher_season_stats(player_id, season):
    try:
        url = MLB_API + "/people/" + str(player_id) + "/stats"
        params = {"stats": "season", "group": "pitching", "season": season, "sportId": 1}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        splits = data.get("stats", [{}])[0].get("splits", [])
        if not splits:
            return None
        s = splits[0].get("stat", {})
        ip = float(s.get("inningsPitched", 0) or 0)
        so = int(s.get("strikeOuts", 0) or 0)
        gs = int(s.get("gamesStarted", 0) or 0)
        k9 = round(so / ip * 9, 2) if ip > 0 else 0.0
        k_pct = round(float(s.get("strikeoutPercentage", 0) or 0), 4)
        era = float(s.get("era", LEAGUE_AVG_ERA) or LEAGUE_AVG_ERA)
        whip = float(s.get("whip", 1.30) or 1.30)
        avg_ip = round(ip / max(gs, 1), 2)
        return {"k9": k9, "k_pct": k_pct, "era": era, "whip": whip, "innings_pitched": ip, "strikeouts": so, "games_started": gs, "avg_innings_per_start": avg_ip, "season": season}
    except Exception as e:
        logger.error("Season stats failed for " + str(player_id) + " season " + str(season) + ": " + str(e))
        return None
 
 
def get_pitcher_recent_stats(player_id, num_starts=5):
    try:
        url = MLB_API + "/people/" + str(player_id) + "/stats"
        params = {"stats": "gameLog", "group": "pitching", "season": CURRENT_YEAR, "sportId": 1}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        splits = data.get("stats", [{}])[0].get("splits", [])
        starts = [s for s in splits if int(s.get("stat", {}).get("gamesStarted", 0) or 0) > 0]
        recent = starts[-num_starts:] if len(starts) >= num_starts else starts
        if not recent:
            return None
        total_weight = 0
        weighted_k = 0.0
        weighted_ip = 0.0
        weighted_era = 0.0
        for i, start in enumerate(recent):
            weight = i + 1
            stat = start.get("stat", {})
            ks = int(stat.get("strikeOuts", 0) or 0)
            ip = float(stat.get("inningsPitched", 0) or 0)
            era = float(stat.get("era", LEAGUE_AVG_ERA) or LEAGUE_AVG_ERA)
            weighted_k += ks * weight
            weighted_ip += ip * weight
            weighted_era += era * weight
            total_weight += weight
        avg_k = round(weighted_k / total_weight, 2) if total_weight > 0 else 0
        avg_ip = round(weighted_ip / total_weight, 2) if total_weight > 0 else 0
        avg_era = round(weighted_era / total_weight, 2) if total_weight > 0 else LEAGUE_AVG_ERA
        k9_recent = round(avg_k / avg_ip * 9, 2) if avg_ip > 0 else 0
        return {"avg_k_recent": avg_k, "avg_ip_recent": avg_ip, "k9_recent": k9_recent, "era_recent": avg_era, "starts_sampled": len(recent)}
    except Exception as e:
        logger.error("Recent stats failed for " + str(player_id) + ": " + str(e))
        return None
 
 
def get_pitcher_splits(player_id):
    try:
        url = MLB_API + "/people/" + str(player_id) + "/stats"
        params = {"stats": "statSplits", "group": "pitching", "season": CURRENT_YEAR, "sportId": 1, "sitCodes": "vl,vr"}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        splits_data = {"vs_lhb": {"k_pct": 0.22, "era": LEAGUE_AVG_ERA}, "vs_rhb": {"k_pct": 0.22, "era": LEAGUE_AVG_ERA}}
        for stat_group in data.get("stats", []):
            for split in stat_group.get("splits", []):
                split_code = split.get("split", {}).get("code", "")
                stat = split.get("stat", {})
                ip = float(stat.get("inningsPitched", 0) or 0)
                so = int(stat.get("strikeOuts", 0) or 0)
                era = float(stat.get("era", LEAGUE_AVG_ERA) or LEAGUE_AVG_ERA)
                k_pct = round(so / max(ip * 3, 1), 4)
                if split_code == "vl":
                    splits_data["vs_lhb"] = {"k_pct": k_pct, "era": era, "ip": ip}
                elif split_code == "vr":
                    splits_data["vs_rhb"] = {"k_pct": k_pct, "era": era, "ip": ip}
        logger.info("Splits for " + str(player_id) + ": vsL=" + str(splits_data["vs_lhb"]["k_pct"]) + " vsR=" + str(splits_data["vs_rhb"]["k_pct"]))
        return splits_data
    except Exception as e:
        logger.error("Splits failed for " + str(player_id) + ": " + str(e))
        return {"vs_lhb": {"k_pct": 0.22, "era": LEAGUE_AVG_ERA}, "vs_rhb": {"k_pct": 0.22, "era": LEAGUE_AVG_ERA}}
 
 
def get_todays_lineup(team_name):
    try:
        url = MLB_API + "/schedule"
        params = {"sportId": 1, "hydrate": "lineups,team", "date": _today_str()}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        for date in data.get("dates", []):
            for game in date.get("games", []):
                home = game.get("teams", {}).get("home", {})
                away = game.get("teams", {}).get("away", {})
                home_name = home.get("team", {}).get("name", "")
                away_name = away.get("team", {}).get("name", "")
                for side, team_data, name in [("home", home, home_name), ("away", away, away_name)]:
                    if team_name.lower() in name.lower():
                        lineups = game.get("lineups", {})
                        side_lineup = lineups.get("homePlayers" if side == "home" else "awayPlayers", [])
                        if side_lineup:
                            lineup_ids = [p.get("id") for p in side_lineup if p.get("id")]
                            logger.info("Got lineup for " + team_name + ": " + str(len(lineup_ids)) + " players")
                            return lineup_ids
        logger.warning("No lineup available yet for " + team_name)
        return []
    except Exception as e:
        logger.error("Lineup fetch failed for " + team_name + ": " + str(e))
        return []
 
 
def get_batter_handedness(player_id):
    try:
        url = MLB_API + "/people/" + str(player_id)
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        people = resp.json().get("people", [{}])
        hand = people[0].get("batSide", {}).get("code", "R")
        return hand
    except Exception:
        return "R"
 
 
def get_lineup_platoon_composition(team_name):
    try:
        lineup_ids = get_todays_lineup(team_name)
        if not lineup_ids:
            logger.warning("No lineup for " + team_name + " - using league average splits")
            return {"lhb_pct": 0.42, "rhb_pct": 0.58, "lineup_available": False}
        lhb = 0
        rhb = 0
        for pid in lineup_ids[:9]:
            hand = get_batter_handedness(pid)
            if hand == "L":
                lhb += 1
            else:
                rhb += 1
        total = max(lhb + rhb, 1)
        lhb_pct = round(lhb / total, 3)
        rhb_pct = round(rhb / total, 3)
        logger.info(team_name + " lineup: " + str(lhb) + " LHB + " + str(rhb) + " RHB")
        return {"lhb_pct": lhb_pct, "rhb_pct": rhb_pct, "lhb_count": lhb, "rhb_count": rhb, "lineup_available": True}
    except Exception as e:
        logger.error("Platoon composition failed for " + team_name + ": " + str(e))
        return {"lhb_pct": 0.42, "rhb_pct": 0.58, "lineup_available": False}
 
 
def get_platoon_k_adjustment(pitcher_hand, lineup_composition, pitcher_splits):
    try:
        lhb_pct = lineup_composition.get("lhb_pct", 0.42)
        rhb_pct = lineup_composition.get("rhb_pct", 0.58)
        vs_lhb_k = pitcher_splits.get("vs_lhb", {}).get("k_pct", 0.22)
        vs_rhb_k = pitcher_splits.get("vs_rhb", {}).get("k_pct", 0.22)
        LEAGUE_AVG_K = 0.225
        lhb_adj = vs_lhb_k / LEAGUE_AVG_K if vs_lhb_k > 0 else 1.0
        rhb_adj = vs_rhb_k / LEAGUE_AVG_K if vs_rhb_k > 0 else 1.0
        weighted_adj = (lhb_adj * lhb_pct) + (rhb_adj * rhb_pct)
        weighted_adj = max(0.80, min(1.20, weighted_adj))
        logger.info("Platoon adj: pitcher=" + pitcher_hand + " lhb_pct=" + str(lhb_pct) + " vsL_k=" + str(vs_lhb_k) + " vsR_k=" + str(vs_rhb_k) + " adj=" + str(round(weighted_adj, 4)))
        return round(weighted_adj, 4)
    except Exception as e:
        logger.error("Platoon adjustment failed: " + str(e))
        return 1.0
 
 
def get_blended_pitcher_stats(player_id):
    current = get_pitcher_season_stats(player_id, CURRENT_YEAR)
    last = get_pitcher_season_stats(player_id, LAST_YEAR)
    recent = get_pitcher_recent_stats(player_id, num_starts=5)
    current_starts = current.get("games_started", 0) if current else 0
    cw, lw = get_season_weight(current_starts)
    logger.info("Blending " + str(player_id) + ": " + str(current_starts) + " starts cw=" + str(cw) + " lw=" + str(lw))
    if not current and not last:
        return _fallback_stats()
    if not last:
        cw, lw = 1.0, 0.0
    if not current:
        cw, lw = 0.0, 1.0
    k9_current = current.get("k9", 8.0) if current else 8.0
    k9_last = last.get("k9", 8.0) if last else 8.0
    k9_blended = round((k9_current * cw) + (k9_last * lw), 3)
    era_current = current.get("era", LEAGUE_AVG_ERA) if current else LEAGUE_AVG_ERA
    era_last = last.get("era", LEAGUE_AVG_ERA) if last else LEAGUE_AVG_ERA
    era_blended = round((era_current * cw) + (era_last * lw), 3)
    kpct_current = current.get("k_pct", 0.22) if current else 0.22
    kpct_last = last.get("k_pct", 0.22) if last else 0.22
    kpct_blended = round((kpct_current * cw) + (kpct_last * lw), 4)
    ip_current = current.get("avg_innings_per_start", 5.5) if current else 5.5
    ip_last = last.get("avg_innings_per_start", 5.5) if last else 5.5
    ip_blended = round((ip_current * cw) + (ip_last * lw), 2)
    if recent and current_starts >= 3:
        k9_final = round((k9_blended * 0.80) + (recent.get("k9_recent", k9_blended) * 0.20), 3)
        era_final = round((era_blended * 0.80) + (recent.get("era_recent", era_blended) * 0.20), 3)
        ip_final = round((ip_blended * 0.80) + (recent.get("avg_ip_recent", ip_blended) * 0.20), 2)
    else:
        k9_final = k9_blended
        era_final = era_blended
        ip_final = ip_blended
    logger.info("Blended: K9=" + str(k9_final) + " ERA=" + str(era_final) + " IP=" + str(ip_final))
    return {"k9": k9_final, "k_pct": kpct_blended, "era": era_final, "avg_innings_per_start": ip_final, "games_started_current": current_starts, "current_weight": cw, "last_season_weight": lw, "k9_current": k9_current, "k9_last": k9_last, "era_current": era_current, "era_last": era_last}
 
 
def get_pitcher_handedness(player_id):
    try:
        url = MLB_API + "/people/" + str(player_id)
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        people = resp.json().get("people", [{}])
        hand = people[0].get("pitchHand", {}).get("code", "R")
        return hand
    except Exception:
        return "R"
 
 
def get_team_k_rate(team_name):
    try:
        url = MLB_API + "/teams"
        params = {"sportId": 1, "season": CURRENT_YEAR}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        teams = resp.json().get("teams", [])
        team_id = None
        for t in teams:
            if team_name.lower() in t.get("name", "").lower():
                team_id = t["id"]
                break
        if not team_id:
            return {"k_pct": LEAGUE_AVG_K_PCT, "k_adjustment": 1.0}
        current_k = _get_team_k_for_season(team_id, CURRENT_YEAR)
        last_k = _get_team_k_for_season(team_id, LAST_YEAR)
        current_k_pct = current_k or LEAGUE_AVG_K_PCT
        last_k_pct = last_k or LEAGUE_AVG_K_PCT
        from datetime import date
        day_of_year = date.today().timetuple().tm_yday
        days_into_season = max(0, day_of_year - 80)
        if days_into_season < 20:
            cw, lw = 0.30, 0.70
        elif days_into_season < 40:
            cw, lw = 0.50, 0.50
        elif days_into_season < 70:
            cw, lw = 0.70, 0.30
        else:
            cw, lw = 0.85, 0.15
        blended_k_pct = round((current_k_pct * cw) + (last_k_pct * lw), 4)
        k_adjustment = round(blended_k_pct / LEAGUE_AVG_K_PCT, 4)
        logger.info(team_name + " K%=" + str(blended_k_pct) + " adj=" + str(k_adjustment))
        return {"k_pct": blended_k_pct, "k_adjustment": k_adjustment, "team_id": team_id}
    except Exception as e:
        logger.error("Team K rate failed for " + team_name + ": " + str(e))
        return {"k_pct": LEAGUE_AVG_K_PCT, "k_adjustment": 1.0}
 
 
def _get_team_k_for_season(team_id, season):
    try:
        url = MLB_API + "/teams/" + str(team_id) + "/stats"
        params = {"stats": "season", "group": "hitting", "season": season}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        splits = data.get("stats", [{}])[0].get("splits", [])
        if not splits:
            return None
        stat = splits[0].get("stat", {})
        return float(stat.get("strikeoutPercentage", LEAGUE_AVG_K_PCT) or LEAGUE_AVG_K_PCT)
    except Exception:
        return None
 
 
def get_full_pitcher_profile(player_name, opponent_team, home_team):
    logger.info("Building profile for " + player_name + " vs " + opponent_team)
    player_id = get_pitcher_id(player_name)
    if not player_id:
        logger.warning("Could not find " + player_name + " - using fallback")
        return _fallback_profile()
    blended = get_blended_pitcher_stats(player_id)
    opp_k = get_team_k_rate(opponent_team)
    hand = get_pitcher_handedness(player_id)
    splits = get_pitcher_splits(player_id)
    lineup = get_lineup_platoon_composition(opponent_team)
    platoon_adj = get_platoon_k_adjustment(hand, lineup, splits)
    profile = {
        "player_name": player_name,
        "player_id": player_id,
        "hand": hand,
        "k9_season": blended.get("k9", 8.0),
        "k_pct_season": blended.get("k_pct", 0.22),
        "era": blended.get("era", LEAGUE_AVG_ERA),
        "avg_ip_season": blended.get("avg_innings_per_start", 5.5),
        "k9_recent": blended.get("k9", 8.0),
        "avg_k_recent": round(blended.get("k9", 8.0) / 9 * blended.get("avg_innings_per_start", 5.5), 2),
        "avg_ip_recent": blended.get("avg_innings_per_start", 5.5),
        "opp_k_pct": opp_k.get("k_pct", LEAGUE_AVG_K_PCT),
        "opp_k_adjustment": opp_k.get("k_adjustment", 1.0),
        "platoon_adjustment": platoon_adj,
        "lineup_available": lineup.get("lineup_available", False),
        "opponent_team": opponent_team,
        "home_team": home_team,
        "current_season_weight": blended.get("current_weight", 0.40),
        "last_season_weight": blended.get("last_season_weight", 0.60),
        "games_started_current": blended.get("games_started_current", 0),
    }
    logger.info("Profile: K9=" + str(profile["k9_season"]) + " ERA=" + str(profile["era"]) + " oppAdj=" + str(profile["opp_k_adjustment"]) + " platoonAdj=" + str(platoon_adj) + " lineupAvail=" + str(lineup.get("lineup_available")))
    return profile
 
 
def _fallback_stats():
    return {"k9": 8.0, "k_pct": 0.22, "era": LEAGUE_AVG_ERA, "avg_innings_per_start": 5.5, "games_started_current": 0, "current_weight": 0.20, "last_season_weight": 0.80}
 
 
def _fallback_profile():
    return {"player_name": "Unknown", "player_id": None, "hand": "R", "k9_season": 8.0, "k_pct_season": 0.22, "era": LEAGUE_AVG_ERA, "avg_ip_season": 5.5, "k9_recent": 8.0, "avg_k_recent": 5.0, "avg_ip_recent": 5.5, "opp_k_pct": LEAGUE_AVG_K_PCT, "opp_k_adjustment": 1.0, "platoon_adjustment": 1.0, "lineup_available": False, "opponent_team": "Unknown", "home_team": "Unknown", "current_season_weight": 0.20, "last_season_weight": 0.80, "games_started_current": 0}
import logging
from datetime import datetime, timedelta
 
logger = logging.getLogger(__name__)
MLB_API = "https://statsapi.mlb.com/api/v1"
CURRENT_YEAR = datetime.now().year
LAST_YEAR = CURRENT_YEAR - 1
LEAGUE_AVG_K_PCT = 0.225
LEAGUE_AVG_ERA = 4.25
 
 
def _today_str():
    return datetime.now().strftime("%Y-%m-%d")
 
 
def get_season_weight(current_starts):
    if current_starts <= 3:
        return 0.20, 0.80
    elif current_starts <= 6:
        return 0.40, 0.60
    elif current_starts <= 10:
        return 0.60, 0.40
    elif current_starts <= 15:
        return 0.75, 0.25
    else:
        return 0.90, 0.10
 
 
def get_pitcher_id(player_name):
    try:
        url = MLB_API + "/people/search"
        params = {"names": player_name, "sportId": 1}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        people = resp.json().get("people", [])
        if people:
            pid = people[0]["id"]
            logger.info("Found " + player_name + ": ID=" + str(pid))
            return pid
        logger.warning("Player not found: " + player_name)
        return None
    except Exception as e:
        logger.error("Player lookup failed for " + player_name + ": " + str(e))
        return None
 
 
def get_pitcher_season_stats(player_id, season):
    try:
        url = MLB_API + "/people/" + str(player_id) + "/stats"
        params = {"stats": "season", "group": "pitching", "season": season, "sportId": 1}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        splits = data.get("stats", [{}])[0].get("splits", [])
        if not splits:
            return None
        s = splits[0].get("stat", {})
        ip = float(s.get("inningsPitched", 0) or 0)
        so = int(s.get("strikeOuts", 0) or 0)
        gs = int(s.get("gamesStarted", 0) or 0)
        k9 = round(so / ip * 9, 2) if ip > 0 else 0.0
        k_pct = round(float(s.get("strikeoutPercentage", 0) or 0), 4)
        era = float(s.get("era", LEAGUE_AVG_ERA) or LEAGUE_AVG_ERA)
        whip = float(s.get("whip", 1.30) or 1.30)
        avg_ip = round(ip / max(gs, 1), 2)
        return {"k9": k9, "k_pct": k_pct, "era": era, "whip": whip, "innings_pitched": ip, "strikeouts": so, "games_started": gs, "avg_innings_per_start": avg_ip, "season": season}
    except Exception as e:
        logger.error("Season stats failed for " + str(player_id) + " season " + str(season) + ": " + str(e))
        return None
 
 
def get_pitcher_recent_stats(player_id, num_starts=5):
    try:
        url = MLB_API + "/people/" + str(player_id) + "/stats"
        params = {"stats": "gameLog", "group": "pitching", "season": CURRENT_YEAR, "sportId": 1}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        splits = data.get("stats", [{}])[0].get("splits", [])
        starts = [s for s in splits if int(s.get("stat", {}).get("gamesStarted", 0) or 0) > 0]
        recent = starts[-num_starts:] if len(starts) >= num_starts else starts
        if not recent:
            return None
        total_weight = 0
        weighted_k = 0.0
        weighted_ip = 0.0
        weighted_era = 0.0
        for i, start in enumerate(recent):
            weight = i + 1
            stat = start.get("stat", {})
            ks = int(stat.get("strikeOuts", 0) or 0)
            ip = float(stat.get("inningsPitched", 0) or 0)
            era = float(stat.get("era", LEAGUE_AVG_ERA) or LEAGUE_AVG_ERA)
            weighted_k += ks * weight
            weighted_ip += ip * weight
            weighted_era += era * weight
            total_weight += weight
        avg_k = round(weighted_k / total_weight, 2) if total_weight > 0 else 0
        avg_ip = round(weighted_ip / total_weight, 2) if total_weight > 0 else 0
        avg_era = round(weighted_era / total_weight, 2) if total_weight > 0 else LEAGUE_AVG_ERA
        k9_recent = round(avg_k / avg_ip * 9, 2) if avg_ip > 0 else 0
        return {"avg_k_recent": avg_k, "avg_ip_recent": avg_ip, "k9_recent": k9_recent, "era_recent": avg_era, "starts_sampled": len(recent)}
    except Exception as e:
        logger.error("Recent stats failed for " + str(player_id) + ": " + str(e))
        return None
 
 
def get_pitcher_splits(player_id):
    try:
        url = MLB_API + "/people/" + str(player_id) + "/stats"
        params = {"stats": "statSplits", "group": "pitching", "season": CURRENT_YEAR, "sportId": 1, "sitCodes": "vl,vr"}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        splits_data = {"vs_lhb": {"k_pct": 0.22, "era": LEAGUE_AVG_ERA}, "vs_rhb": {"k_pct": 0.22, "era": LEAGUE_AVG_ERA}}
        for stat_group in data.get("stats", []):
            for split in stat_group.get("splits", []):
                split_code = split.get("split", {}).get("code", "")
                stat = split.get("stat", {})
                ip = float(stat.get("inningsPitched", 0) or 0)
                so = int(stat.get("strikeOuts", 0) or 0)
                era = float(stat.get("era", LEAGUE_AVG_ERA) or LEAGUE_AVG_ERA)
                k_pct = round(so / max(ip * 3, 1), 4)
                if split_code == "vl":
                    splits_data["vs_lhb"] = {"k_pct": k_pct, "era": era, "ip": ip}
                elif split_code == "vr":
                    splits_data["vs_rhb"] = {"k_pct": k_pct, "era": era, "ip": ip}
        logger.info("Splits for " + str(player_id) + ": vsL=" + str(splits_data["vs_lhb"]["k_pct"]) + " vsR=" + str(splits_data["vs_rhb"]["k_pct"]))
        return splits_data
    except Exception as e:
        logger.error("Splits failed for " + str(player_id) + ": " + str(e))
        return {"vs_lhb": {"k_pct": 0.22, "era": LEAGUE_AVG_ERA}, "vs_rhb": {"k_pct": 0.22, "era": LEAGUE_AVG_ERA}}
 
 
def get_todays_lineup(team_name):
    try:
        url = MLB_API + "/schedule"
        params = {"sportId": 1, "hydrate": "lineups,team", "date": _today_str()}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        for date in data.get("dates", []):
            for game in date.get("games", []):
                home = game.get("teams", {}).get("home", {})
                away = game.get("teams", {}).get("away", {})
                home_name = home.get("team", {}).get("name", "")
                away_name = away.get("team", {}).get("name", "")
                for side, team_data, name in [("home", home, home_name), ("away", away, away_name)]:
                    if team_name.lower() in name.lower():
                        lineups = game.get("lineups", {})
                        side_lineup = lineups.get("homePlayers" if side == "home" else "awayPlayers", [])
                        if side_lineup:
                            lineup_ids = [p.get("id") for p in side_lineup if p.get("id")]
                            logger.info("Got lineup for " + team_name + ": " + str(len(lineup_ids)) + " players")
                            return lineup_ids
        logger.warning("No lineup available yet for " + team_name)
        return []
    except Exception as e:
        logger.error("Lineup fetch failed for " + team_name + ": " + str(e))
        return []
 
 
def get_batter_handedness(player_id):
    try:
        url = MLB_API + "/people/" + str(player_id)
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        people = resp.json().get("people", [{}])
        hand = people[0].get("batSide", {}).get("code", "R")
        return hand
    except Exception:
        return "R"
 
 
def get_lineup_platoon_composition(team_name):
    try:
        lineup_ids = get_todays_lineup(team_name)
        if not lineup_ids:
            logger.warning("No lineup for " + team_name + " - using league average splits")
            return {"lhb_pct": 0.42, "rhb_pct": 0.58, "lineup_available": False}
        lhb = 0
        rhb = 0
        for pid in lineup_ids[:9]:
            hand = get_batter_handedness(pid)
            if hand == "L":
                lhb += 1
            else:
                rhb += 1
        total = max(lhb + rhb, 1)
        lhb_pct = round(lhb / total, 3)
        rhb_pct = round(rhb / total, 3)
        logger.info(team_name + " lineup: " + str(lhb) + " LHB + " + str(rhb) + " RHB")
        return {"lhb_pct": lhb_pct, "rhb_pct": rhb_pct, "lhb_count": lhb, "rhb_count": rhb, "lineup_available": True}
    except Exception as e:
        logger.error("Platoon composition failed for " + team_name + ": " + str(e))
        return {"lhb_pct": 0.42, "rhb_pct": 0.58, "lineup_available": False}
 
 
def get_platoon_k_adjustment(pitcher_hand, lineup_composition, pitcher_splits):
    try:
        lhb_pct = lineup_composition.get("lhb_pct", 0.42)
        rhb_pct = lineup_composition.get("rhb_pct", 0.58)
        vs_lhb_k = pitcher_splits.get("vs_lhb", {}).get("k_pct", 0.22)
        vs_rhb_k = pitcher_splits.get("vs_rhb", {}).get("k_pct", 0.22)
        LEAGUE_AVG_K = 0.225
        lhb_adj = vs_lhb_k / LEAGUE_AVG_K if vs_lhb_k > 0 else 1.0
        rhb_adj = vs_rhb_k / LEAGUE_AVG_K if vs_rhb_k > 0 else 1.0
        weighted_adj = (lhb_adj * lhb_pct) + (rhb_adj * rhb_pct)
        weighted_adj = max(0.80, min(1.20, weighted_adj))
        logger.info("Platoon adj: pitcher=" + pitcher_hand + " lhb_pct=" + str(lhb_pct) + " vsL_k=" + str(vs_lhb_k) + " vsR_k=" + str(vs_rhb_k) + " adj=" + str(round(weighted_adj, 4)))
        return round(weighted_adj, 4)
    except Exception as e:
        logger.error("Platoon adjustment failed: " + str(e))
        return 1.0
 
 
def get_blended_pitcher_stats(player_id):
    current = get_pitcher_season_stats(player_id, CURRENT_YEAR)
    last = get_pitcher_season_stats(player_id, LAST_YEAR)
    recent = get_pitcher_recent_stats(player_id, num_starts=5)
    current_starts = current.get("games_started", 0) if current else 0
    cw, lw = get_season_weight(current_starts)
    logger.info("Blending " + str(player_id) + ": " + str(current_starts) + " starts cw=" + str(cw) + " lw=" + str(lw))
    if not current and not last:
        return _fallback_stats()
    if not last:
        cw, lw = 1.0, 0.0
    if not current:
        cw, lw = 0.0, 1.0
    k9_current = current.get("k9", 8.0) if current else 8.0
    k9_last = last.get("k9", 8.0) if last else 8.0
    k9_blended = round((k9_current * cw) + (k9_last * lw), 3)
    era_current = current.get("era", LEAGUE_AVG_ERA) if current else LEAGUE_AVG_ERA
    era_last = last.get("era", LEAGUE_AVG_ERA) if last else LEAGUE_AVG_ERA
    era_blended = round((era_current * cw) + (era_last * lw), 3)
    kpct_current = current.get("k_pct", 0.22) if current else 0.22
    kpct_last = last.get("k_pct", 0.22) if last else 0.22
    kpct_blended = round((kpct_current * cw) + (kpct_last * lw), 4)
    ip_current = current.get("avg_innings_per_start", 5.5) if current else 5.5
    ip_last = last.get("avg_innings_per_start", 5.5) if last else 5.5
    ip_blended = round((ip_current * cw) + (ip_last * lw), 2)
    if recent and current_starts >= 3:
        k9_final = round((k9_blended * 0.80) + (recent.get("k9_recent", k9_blended) * 0.20), 3)
        era_final = round((era_blended * 0.80) + (recent.get("era_recent", era_blended) * 0.20), 3)
        ip_final = round((ip_blended * 0.80) + (recent.get("avg_ip_recent", ip_blended) * 0.20), 2)
    else:
        k9_final = k9_blended
        era_final = era_blended
        ip_final = ip_blended
    logger.info("Blended: K9=" + str(k9_final) + " ERA=" + str(era_final) + " IP=" + str(ip_final))
    return {"k9": k9_final, "k_pct": kpct_blended, "era": era_final, "avg_innings_per_start": ip_final, "games_started_current": current_starts, "current_weight": cw, "last_season_weight": lw, "k9_current": k9_current, "k9_last": k9_last, "era_current": era_current, "era_last": era_last}
 
 
def get_pitcher_handedness(player_id):
    try:
        url = MLB_API + "/people/" + str(player_id)
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        people = resp.json().get("people", [{}])
        hand = people[0].get("pitchHand", {}).get("code", "R")
        return hand
    except Exception:
        return "R"
 
 
def get_team_k_rate(team_name):
    try:
        url = MLB_API + "/teams"
        params = {"sportId": 1, "season": CURRENT_YEAR}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        teams = resp.json().get("teams", [])
        team_id = None
        for t in teams:
            if team_name.lower() in t.get("name", "").lower():
                team_id = t["id"]
                break
        if not team_id:
            return {"k_pct": LEAGUE_AVG_K_PCT, "k_adjustment": 1.0}
        current_k = _get_team_k_for_season(team_id, CURRENT_YEAR)
        last_k = _get_team_k_for_season(team_id, LAST_YEAR)
        current_k_pct = current_k or LEAGUE_AVG_K_PCT
        last_k_pct = last_k or LEAGUE_AVG_K_PCT
        from datetime import date
        day_of_year = date.today().timetuple().tm_yday
        days_into_season = max(0, day_of_year - 80)
        if days_into_season < 20:
            cw, lw = 0.30, 0.70
        elif days_into_season < 40:
            cw, lw = 0.50, 0.50
        elif days_into_season < 70:
            cw, lw = 0.70, 0.30
        else:
            cw, lw = 0.85, 0.15
        blended_k_pct = round((current_k_pct * cw) + (last_k_pct * lw), 4)
        k_adjustment = round(blended_k_pct / LEAGUE_AVG_K_PCT, 4)
        logger.info(team_name + " K%=" + str(blended_k_pct) + " adj=" + str(k_adjustment))
        return {"k_pct": blended_k_pct, "k_adjustment": k_adjustment, "team_id": team_id}
    except Exception as e:
        logger.error("Team K rate failed for " + team_name + ": " + str(e))
        return {"k_pct": LEAGUE_AVG_K_PCT, "k_adjustment": 1.0}
 
 
def _get_team_k_for_season(team_id, season):
    try:
        url = MLB_API + "/teams/" + str(team_id) + "/stats"
        params = {"stats": "season", "group": "hitting", "season": season}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        splits = data.get("stats", [{}])[0].get("splits", [])
        if not splits:
            return None
        stat = splits[0].get("stat", {})
        return float(stat.get("strikeoutPercentage", LEAGUE_AVG_K_PCT) or LEAGUE_AVG_K_PCT)
    except Exception:
        return None
 
 
def get_full_pitcher_profile(player_name, opponent_team, home_team):
    logger.info("Building profile for " + player_name + " vs " + opponent_team)
    player_id = get_pitcher_id(player_name)
    if not player_id:
        logger.warning("Could not find " + player_name + " - using fallback")
        return _fallback_profile()
    blended = get_blended_pitcher_stats(player_id)
    opp_k = get_team_k_rate(opponent_team)
    hand = get_pitcher_handedness(player_id)
    splits = get_pitcher_splits(player_id)
    lineup = get_lineup_platoon_composition(opponent_team)
    platoon_adj = get_platoon_k_adjustment(hand, lineup, splits)
    profile = {
        "player_name": player_name,
        "player_id": player_id,
        "hand": hand,
        "k9_season": blended.get("k9", 8.0),
        "k_pct_season": blended.get("k_pct", 0.22),
        "era": blended.get("era", LEAGUE_AVG_ERA),
        "avg_ip_season": blended.get("avg_innings_per_start", 5.5),
        "k9_recent": blended.get("k9", 8.0),
        "avg_k_recent": round(blended.get("k9", 8.0) / 9 * blended.get("avg_innings_per_start", 5.5), 2),
        "avg_ip_recent": blended.get("avg_innings_per_start", 5.5),
        "opp_k_pct": opp_k.get("k_pct", LEAGUE_AVG_K_PCT),
        "opp_k_adjustment": opp_k.get("k_adjustment", 1.0),
        "platoon_adjustment": platoon_adj,
        "lineup_available": lineup.get("lineup_available", False),
        "opponent_team": opponent_team,
        "home_team": home_team,
        "current_season_weight": blended.get("current_weight", 0.40),
        "last_season_weight": blended.get("last_season_weight", 0.60),
        "games_started_current": blended.get("games_started_current", 0),
    }
    logger.info("Profile: K9=" + str(profile["k9_season"]) + " ERA=" + str(profile["era"]) + " oppAdj=" + str(profile["opp_k_adjustment"]) + " platoonAdj=" + str(platoon_adj) + " lineupAvail=" + str(lineup.get("lineup_available")))
    return profile
 
 
def _fallback_stats():
    return {"k9": 8.0, "k_pct": 0.22, "era": LEAGUE_AVG_ERA, "avg_innings_per_start": 5.5, "games_started_current": 0, "current_weight": 0.20, "last_season_weight": 0.80}
 
 
def _fallback_profile():
    return {"player_name": "Unknown", "player_id": None, "hand": "R", "k9_season": 8.0, "k_pct_season": 0.22, "era": LEAGUE_AVG_ERA, "avg_ip_season": 5.5, "k9_recent": 8.0, "avg_k_recent": 5.0, "avg_ip_recent": 5.5, "opp_k_pct": LEAGUE_AVG_K_PCT, "opp_k_adjustment": 1.0, "platoon_adjustment": 1.0, "lineup_available": False, "opponent_team": "Unknown", "home_team": "Unknown", "current_season_weight": 0.20, "last_season_weight": 0.80, "games_started_current": 0}
