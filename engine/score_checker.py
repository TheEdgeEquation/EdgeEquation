import requests
import logging
from datetime import datetime
from engine.data_tracker import load_plays, save_results

logger = logging.getLogger(__name__)

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"

SPORT_CONFIG = {
    "baseball_mlb": {
        "espn_sport": "baseball",
        "espn_league": "mlb",
        "stat_keys": ["pitchingStrikeouts", "strikeOuts", "SO"],
    },
    "basketball_nba": {
        "espn_sport": "basketball",
        "espn_league": "nba",
        "stat_keys": ["threePointFieldGoalsMade", "3PM"],
    },
    "icehockey_nhl": {
        "espn_sport": "hockey",
        "espn_league": "nhl",
        "stat_keys": ["shotsOnGoal", "shots", "SOG"],
    },
    "americanfootball_nfl": {
        "espn_sport": "football",
        "espn_league": "nfl",
        "stat_keys": ["receptions", "REC"],
    },
}


def _get_scoreboard(sport, league, date_str):
    url = f"{ESPN_BASE}/{sport}/{league}/scoreboard"
    try:
        resp = requests.get(url, params={"dates": date_str, "limit": 20}, timeout=15)
        resp.raise_for_status()
        events = resp.json().get("events", [])
        logger.info(f"[{league}] {len(events)} events for {date_str}")
        return events
    except Exception as e:
        logger.error(f"[{league}] Scoreboard failed: {e}")
        return []


def _get_box_score(sport, league, game_id):
    url = f"{ESPN_BASE}/{sport}/{league}/summary"
    try:
        resp = requests.get(url, params={"event": game_id}, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Box score failed for {game_id}: {e}")
        return {}


def _find_player_stat(box_score, player_name, stat_keys):
    player_name_lower = player_name.lower()
    for team in box_score.get("boxscore", {}).get("players", []):
        for stat_group in team.get("statistics", []):
            keys = stat_group.get("keys", [])
            labels = stat_group.get("labels", [])
            for athlete_data in stat_group.get("athletes", []):
                athlete = athlete_data.get("athlete", {})
                name = athlete.get("displayName", "").lower()
                short_name = athlete.get("shortName", "").lower()
                if player_name_lower in name or player_name_lower in short_name:
                    stats = athlete_data.get("stats", [])
                    for stat_key in stat_keys:
                        for key_list in [keys, labels]:
                            if stat_key in key_list:
                                idx = key_list.index(stat_key)
                                if idx < len(stats):
                                    try:
                                        return float(stats[idx])
                                    except (ValueError, TypeError):
                                        pass
                    logger.warning(f"Found {name} but stat not in: {keys}")
                    return None
    logger.warning(f"Player '{player_name}' not found in box score")
    return None


def _is_final(event):
    return event.get("status", {}).get("type", {}).get("completed", False)


def check_all_results(style="ee", date_str=None):
    if not date_str:
        date_str = datetime.now().strftime("%Y%m%d")

    plays = load_plays(date_str, style)
    if not plays:
        logger.warning(f"No plays found for {date_str}")
        return []

    logger.info(f"Checking results for {len(plays)} plays")
    all_results = []

    for sport_key, cfg in SPORT_CONFIG.items():
        sport_plays = [p for p in plays if p.get("sport") == sport_key]
        if not sport_plays:
            continue

        sport = cfg["espn_sport"]
        league = cfg["espn_league"]
        stat_keys = cfg["stat_keys"]

        events = _get_scoreboard(sport, league, date_str)
        completed = [e for e in events if _is_final(e)]
        logger.info(f"[{league}] {len(completed)} completed games")

        for play in sport_plays:
            player_name = play.get("player", "")
            line = play.get("line", 0.0)
            matched = False

            for event in completed:
                game_id = event.get("id", "")
                box = _get_box_score(sport, league, game_id)
                actual = _find_player_stat(box, player_name, stat_keys)

                if actual is not None:
                    hit = actual > line
                    logger.info(f"{player_name}: {actual} vs OVER {line} → {'HIT' if hit else 'MISS'}")
                    all_results.append({
                        **play,
                        "hit": hit,
                        "actual_stat": actual,
                        "result_checked": True,
                        "result_note": f"Actual: {actual} vs Line: {line}",
                    })
                    matched = True
                    break

            if not matched:
                logger.warning(f"No result found for {player_name}")
                all_results.append({
                    **play,
                    "hit": None,
                    "actual_stat": None,
                    "result_checked": False,
                    "result_note": "Could not verify",
                })

    if all_results:
        save_results(all_results, style)
        logger.info(f"Results saved: {len(all_results)}")

    return all_results
