"""
engine/stats/mlb_stats.py
Fetches pitcher and team stats from MLB Stats API (free, no key needed).
Used to build true Poisson lambda for strikeout model.
"""
import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

MLB_API = "https://statsapi.mlb.com/api/v1"


def _today_str():
    return datetime.now().strftime("%Y-%m-%d")


def _date_str(days_ago=0):
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def get_pitcher_id(player_name: str) -> int | None:
    """Look up MLB player ID by name."""
    try:
        url = f"{MLB_API}/people/search"
        params = {"names": player_name, "sportId": 1}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        people = resp.json().get("people", [])
        if people:
            pid = people[0]["id"]
            logger.info(f"Found {player_name}: ID={pid}")
            return pid
        logger.warning(f"Player not found: {player_name}")
        return None
    except Exception as e:
        logger.error(f"Player lookup failed for {player_name}: {e}")
        return None


def get_pitcher_season_stats(player_id: int) -> dict:
    """Get pitcher season stats from MLB Stats API."""
    try:
        url = f"{MLB_API}/people/{player_id}/stats"
        params = {
            "stats": "season",
            "group": "pitching",
            "season": datetime.now().year,
            "sportId": 1,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        splits = data.get("stats", [{}])[0].get("splits", [])
        if not splits:
            logger.warning(f"No season stats for player {player_id}")
            return {}

        s = splits[0].get("stat", {})
        ip = float(s.get("inningsPitched", 0) or 0)
        so = int(s.get("strikeOuts", 0) or 0)
        k9 = round(so / ip * 9, 2) if ip > 0 else 0.0
        k_pct = round(float(s.get("strikeoutPercentage", 0) or 0), 4)
        era = float(s.get("era", 4.50) or 4.50)
        whip = float(s.get("whip", 1.30) or 1.30)
        avg_ip = round(ip / max(int(s.get("gamesStarted", 1) or 1), 1), 2)

        stats = {
            "k9": k9,
            "k_pct": k_pct,
            "era": era,
            "whip": whip,
            "innings_pitched": ip,
            "strikeouts": so,
            "games_started": int(s.get("gamesStarted", 0) or 0),
            "avg_innings_per_start": avg_ip,
        }
        logger.info(f"Season stats for {player_id}: K/9={k9}, K%={k_pct}, avgIP={avg_ip}")
        return stats

    except Exception as e:
        logger.error(f"Season stats failed for {player_id}: {e}")
        return {}


def get_pitcher_recent_stats(player_id: int, num_starts: int = 5) -> dict:
    """Get pitcher stats from last N starts — weighted recent form."""
    try:
        url = f"{MLB_API}/people/{player_id}/stats"
        params = {
            "stats": "gameLog",
            "group": "pitching",
            "season": datetime.now().year,
            "sportId": 1,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        splits = data.get("stats", [{}])[0].get("splits", [])
        # Filter to starts only and take last N
        starts = [s for s in splits if int(s.get("stat", {}).get("gamesStarted", 0) or 0) > 0]
        recent = starts[-num_starts:] if len(starts) >= num_starts else starts

        if not recent:
            logger.warning(f"No recent starts for {player_id}")
            return {}

        # Weight recent starts more heavily
        # Most recent = weight 5, oldest = weight 1
        total_weight = 0
        weighted_k = 0.0
        weighted_ip = 0.0

        for i, start in enumerate(recent):
            weight = i + 1  # older=1, newer=N
            stat = start.get("stat", {})
            ks = int(stat.get("strikeOuts", 0) or 0)
            ip = float(stat.get("inningsPitched", 0) or 0)
            weighted_k += ks * weight
            weighted_ip += ip * weight
            total_weight += weight

        avg_k = round(weighted_k / total_weight, 2) if total_weight > 0 else 0
        avg_ip = round(weighted_ip / total_weight, 2) if total_weight > 0 else 0
        k9_recent = round(avg_k / avg_ip * 9, 2) if avg_ip > 0 else 0

        stats = {
            "avg_k_recent": avg_k,
            "avg_ip_recent": avg_ip,
            "k9_recent": k9_recent,
            "starts_sampled": len(recent),
        }
        logger.info(f"Recent {len(recent)} starts for {player_id}: avgK={avg_k}, K/9={k9_recent}")
        return stats

    except Exception as e:
        logger.error(f"Recent stats failed for {player_id}: {e}")
        return {}


def get_team_k_rate(team_name: str) -> dict:
    """Get batting team strikeout rate vs league average."""
    try:
        # Get team ID first
        url = f"{MLB_API}/teams"
        params = {"sportId": 1, "season": datetime.now().year}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        teams = resp.json().get("teams", [])

        team_id = None
        for t in teams:
            if team_name.lower() in t.get("name", "").lower():
                team_id = t["id"]
                break

        if not team_id:
            logger.warning(f"Team not found: {team_name}")
            return {"k_pct": 0.22, "k_adjustment": 1.0}

        # Get team batting stats
        url = f"{MLB_API}/teams/{team_id}/stats"
        params = {
            "stats": "season",
            "group": "hitting",
            "season": datetime.now().year,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        splits = data.get("stats", [{}])[0].get("splits", [])
        if not splits:
            return {"k_pct": 0.22, "k_adjustment": 1.0}

        stat = splits[0].get("stat", {})
        k_pct = float(stat.get("strikeoutPercentage", 0.22) or 0.22)

        # League average K% is ~22.5%
        LEAGUE_AVG_K_PCT = 0.225
        k_adjustment = round(k_pct / LEAGUE_AVG_K_PCT, 4)

        logger.info(f"{team_name} K%={k_pct}, adj={k_adjustment}")
        return {
            "k_pct": k_pct,
            "k_adjustment": k_adjustment,
            "team_id": team_id,
        }

    except Exception as e:
        logger.error(f"Team K rate failed for {team_name}: {e}")
        return {"k_pct": 0.225, "k_adjustment": 1.0}


def get_pitcher_handedness(player_id: int) -> str:
    """Get pitcher throwing hand (L or R)."""
    try:
        url = f"{MLB_API}/people/{player_id}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        people = resp.json().get("people", [{}])
        hand = people[0].get("pitchHand", {}).get("code", "R")
        return hand
    except Exception:
        return "R"


def get_full_pitcher_profile(player_name: str, opponent_team: str, home_team: str) -> dict:
    """
    Build complete pitcher profile for edge calculation.
    Returns all inputs needed for true lambda calculation.
    """
    logger.info(f"Building profile for {player_name} vs {opponent_team}")

    player_id = get_pitcher_id(player_name)
    if not player_id:
        logger.warning(f"Could not find {player_name} — using fallback")
        return _fallback_profile()

    season = get_pitcher_season_stats(player_id)
    recent = get_pitcher_recent_stats(player_id, num_starts=5)
    opp_k = get_team_k_rate(opponent_team)
    hand = get_pitcher_handedness(player_id)

    profile = {
        "player_name": player_name,
        "player_id": player_id,
        "hand": hand,
        "k9_season": season.get("k9", 8.0),
        "k_pct_season": season.get("k_pct", 0.22),
        "era": season.get("era", 4.50),
        "avg_ip_season": season.get("avg_innings_per_start", 5.5),
        "k9_recent": recent.get("k9_recent", season.get("k9", 8.0)),
        "avg_k_recent": recent.get("avg_k_recent", 5.0),
        "avg_ip_recent": recent.get("avg_ip_recent", 5.5),
        "starts_sampled": recent.get("starts_sampled", 0),
        "opp_k_pct": opp_k.get("k_pct", 0.225),
        "opp_k_adjustment": opp_k.get("k_adjustment", 1.0),
        "opponent_team": opponent_team,
        "home_team": home_team,
    }

    logger.info(f"Profile built: K/9={profile['k9_season']}, recentK={profile['avg_k_recent']}, oppAdj={profile['opp_k_adjustment']}")
    return profile


def _fallback_profile() -> dict:
    """Neutral fallback when stats unavailable."""
    return {
        "player_name": "Unknown",
        "player_id": None,
        "hand": "R",
        "k9_season": 8.0,
        "k_pct_season": 0.22,
        "era": 4.50,
        "avg_ip_season": 5.5,
        "k9_recent": 8.0,
        "avg_k_recent": 5.0,
        "avg_ip_recent": 5.5,
        "starts_sampled": 0,
        "opp_k_pct": 0.225,
        "opp_k_adjustment": 1.0,
        "opponent_team": "Unknown",
        "home_team": "Unknown",
    }
