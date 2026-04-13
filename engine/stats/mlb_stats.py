# engine/stats/mlb_stats.py
# Fetches pitcher and team stats from MLB Stats API (free, no key needed).
# Blends current season with last season based on sample size.
# Early season = heavily weighted toward last season.

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
    """
    Returns (current_weight, last_season_weight) based on starts this season.
    Early season heavily favors last season data.
    """
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
        url = f"{MLB_API}/people/search"
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
    """Get pitcher stats for a specific season."""
    try:
        url = f"{MLB_API}/people/{player_id}/stats"
        params = {
            "stats": "season",
            "group": "pitching",
            "season": season,
            "sportId": 1,
        }
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
        return {
            "k9": k9,
            "k_pct": k_pct,
            "era": era,
            "whip": whip,
            "innings_pitched": ip,
            "strikeouts": so,
            "games_started": gs,
            "avg_innings_per_start": avg_ip,
            "season": season,
        }
    except Exception as e:
        logger.error("Season stats failed for " + str(player_id) + " season " + str(season) + ": " + str(e))
        return None


def get_pitcher_recent_stats(player_id, num_starts=5):
    """Get weighted recent form from last N starts this season."""
    try:
        url = f"{MLB_API}/people/{player_id}/stats"
        params = {
            "stats": "gameLog",
            "group": "pitching",
            "season": CURRENT_YEAR,
            "sportId": 1,
        }
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
        return {
            "avg_k_recent": avg_k,
            "avg_ip_recent": avg_ip,
            "k9_recent": k9_recent,
            "era_recent": avg_era,
            "starts_sampled": len(recent),
        }
    except Exception as e:
        logger.error("Recent stats failed for " + str(player_id) + ": " + str(e))
        return None


def get_blended_pitcher_stats(player_id):
    """
    Blend current season + last season stats based on sample size.
    This is the sharp approach for early season accuracy.
    """
    current = get_pitcher_season_stats(player_id, CURRENT_YEAR)
    last = get_pitcher_season_stats(player_id, LAST_YEAR)
    recent = get_pitcher_recent_stats(player_id, num_starts=5)

    current_starts = current.get("games_started", 0) if current else 0
    cw, lw = get_season_weight(current_starts)

    logger.info("Blending stats for " + str(player_id) + ": " + str(current_starts) + " starts this season -> current=" + str(cw) + " last=" + str(lw))

    # Fallbacks
    if not current and not last:
        return _fallback_stats()

    if not last:
        # No last season data - use current only
        cw, lw = 1.0, 0.0
    if not current:
        # No current season data yet - use last season only
        cw, lw = 0.0, 1.0

    # Blend K/9
    k9_current = current.get("k9", 8.0) if current else 8.0
    k9_last = last.get("k9", 8.0) if last else 8.0
    k9_blended = round((k9_current * cw) + (k9_last * lw), 3)

    # Blend ERA
    era_current = current.get("era", LEAGUE_AVG_ERA) if current else LEAGUE_AVG_ERA
    era_last = last.get("era", LEAGUE_AVG_ERA) if last else LEAGUE_AVG_ERA
    era_blended = round((era_current * cw) + (era_last * lw), 3)

    # Blend K%
    kpct_current = current.get("k_pct", 0.22) if current else 0.22
    kpct_last = last.get("k_pct", 0.22) if last else 0.22
    kpct_blended = round((kpct_current * cw) + (kpct_last * lw), 4)

    # Blend avg IP per start
    ip_current = current.get("avg_innings_per_start", 5.5) if current else 5.5
    ip_last = last.get("avg_innings_per_start", 5.5) if last else 5.5
    ip_blended = round((ip_current * cw) + (ip_last * lw), 2)

    # Apply recent form adjustment if available (last 5 starts this season)
    # Recent form gets a 20% nudge on top of blended
    if recent and current_starts >= 3:
        k9_final = round((k9_blended * 0.80) + (recent.get("k9_recent", k9_blended) * 0.20), 3)
        era_final = round((era_blended * 0.80) + (recent.get("era_recent", era_blended) * 0.20), 3)
        ip_final = round((ip_blended * 0.80) + (recent.get("avg_ip_recent", ip_blended) * 0.20), 2)
    else:
        k9_final = k9_blended
        era_final = era_blended
        ip_final = ip_blended

    logger.info("Blended: K/9=" + str(k9_final) + " ERA=" + str(era_final) + " IP=" + str(ip_final))

    return {
        "k9": k9_final,
        "k_pct": kpct_blended,
        "era": era_final,
        "avg_innings_per_start": ip_final,
        "games_started_current": current_starts,
        "current_weight": cw,
        "last_season_weight": lw,
        "k9_current": k9_current,
        "k9_last": k9_last,
        "era_current": era_current,
        "era_last": era_last,
    }


def get_pitcher_handedness(player_id):
    try:
        url = f"{MLB_API}/people/{player_id}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        people = resp.json().get("people", [{}])
        hand = people[0].get("pitchHand", {}).get("code", "R")
        return hand
    except Exception:
        return "R"


def get_team_k_rate(team_name):
    """Get batting team K rate - blended current + last season."""
    try:
        url = f"{MLB_API}/teams"
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

        # Get current season
        current_k = _get_team_k_for_season(team_id, CURRENT_YEAR)
        last_k = _get_team_k_for_season(team_id, LAST_YEAR)

        # Teams need more games to stabilize - use 50/50 early season
        # After ~40 team games (mid May) current season takes over
        current_k_pct = current_k or LEAGUE_AVG_K_PCT
        last_k_pct = last_k or LEAGUE_AVG_K_PCT

        # Early season blend for teams too
        from datetime import date
        day_of_year = date.today().timetuple().tm_yday
        # Season starts ~day 80 (late March)
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
        return {
            "k_pct": blended_k_pct,
            "k_adjustment": k_adjustment,
            "team_id": team_id,
        }
    except Exception as e:
        logger.error("Team K rate failed for " + team_name + ": " + str(e))
        return {"k_pct": LEAGUE_AVG_K_PCT, "k_adjustment": 1.0}


def _get_team_k_for_season(team_id, season):
    try:
        url = f"{MLB_API}/teams/{team_id}/stats"
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
    """Build complete blended pitcher profile for edge calculation."""
    logger.info("Building blended profile for " + player_name + " vs " + opponent_team)

    player_id = get_pitcher_id(player_name)
    if not player_id:
        logger.warning("Could not find " + player_name + " - using fallback")
        return _fallback_profile()

    blended = get_blended_pitcher_stats(player_id)
    opp_k = get_team_k_rate(opponent_team)
    hand = get_pitcher_handedness(player_id)

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
        "opponent_team": opponent_team,
        "home_team": home_team,
        "current_season_weight": blended.get("current_weight", 0.40),
        "last_season_weight": blended.get("last_season_weight", 0.60),
        "games_started_current": blended.get("games_started_current", 0),
    }

    logger.info("Profile: K/9=" + str(profile["k9_season"]) + " ERA=" + str(profile["era"]) + " oppAdj=" + str(profile["opp_k_adjustment"]) + " currentW=" + str(profile["current_season_weight"]))
    return profile


def _fallback_stats():
    return {
        "k9": 8.0,
        "k_pct": 0.22,
        "era": LEAGUE_AVG_ERA,
        "avg_innings_per_start": 5.5,
        "games_started_current": 0,
        "current_weight": 0.20,
        "last_season_weight": 0.80,
    }


def _fallback_profile():
    return {
        "player_name": "Unknown",
        "player_id": None,
        "hand": "R",
        "k9_season": 8.0,
        "k_pct_season": 0.22,
        "era": LEAGUE_AVG_ERA,
        "avg_ip_season": 5.5,
        "k9_recent": 8.0,
        "avg_k_recent": 5.0,
        "avg_ip_recent": 5.5,
        "opp_k_pct": LEAGUE_AVG_K_PCT,
        "opp_k_adjustment": 1.0,
        "opponent_team": "Unknown",
        "home_team": "Unknown",
        "current_season_weight": 0.20,
        "last_season_weight": 0.80,
        "games_started_current": 0,
    }
