import requests
import logging
import csv
import io
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
SAVANT_BASE = "https://baseballsavant.mlb.com"
CURRENT_YEAR = datetime.now().year
LAST_YEAR = CURRENT_YEAR - 1
 
 
def get_pitcher_savant_stats(player_id, season=None):
    if season is None:
        season = CURRENT_YEAR
    try:
        url = SAVANT_BASE + "/statcast_search/csv"
        params = {
            "hfPT": "FF|SL|CU|CH|SI|FC|KC|FS|",
            "hfAB": "",
            "hfBBT": "",
            "hfPR": "",
            "hfZ": "",
            "stadium": "",
            "hfBBL": "",
            "hfNewZones": "",
            "hfGT": "R|",
            "hfC": "",
            "hfSit": "",
            "hfOuts": "",
            "opponent": "",
            "pitcher_throws": "",
            "batter_stands": "",
            "hfSA": "",
            "player_type": "pitcher",
            "hfInfield": "",
            "team": "",
            "position": "",
            "hfOutfield": "",
            "hfRO": "",
            "home_road": "",
            "pitchers_lookup[]": str(player_id),
            "game_date_gt": str(season) + "-03-01",
            "game_date_lt": str(season) + "-11-01",
            "hfFlag": "",
            "hfPull": "",
            "metric_1": "",
            "hfInn": "",
            "min_pitches": "0",
            "min_results": "0",
            "group_by": "name",
            "sort_col": "pitches",
            "player_event_sort": "h_launch_speed",
            "sort_order": "desc",
            "min_pas": "0",
            "type": "details",
        }
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        content = resp.text
        if not content or len(content) < 100:
            logger.warning("No Savant data for pitcher " + str(player_id) + " season " + str(season))
            return None
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        if not rows:
            return None
        total_pitches = len(rows)
        swinging_strikes = sum(1 for r in rows if r.get("description", "") in ("swinging_strike", "swinging_strike_blocked", "foul_tip"))
        swstr_pct = round(swinging_strikes / total_pitches, 4) if total_pitches > 0 else 0.0
        called_strikes = sum(1 for r in rows if r.get("description", "") == "called_strike")
        csw_pct = round((swinging_strikes + called_strikes) / total_pitches, 4) if total_pitches > 0 else 0.0
        pitch_counts = {}
        for r in rows:
            pt = r.get("pitch_type", "")
            if pt:
                pitch_counts[pt] = pitch_counts.get(pt, 0) + 1
        pitch_mix = {k: round(v / total_pitches, 4) for k, v in pitch_counts.items()}
        breaking_pct = sum(v for k, v in pitch_mix.items() if k in ("SL", "CU", "KC", "SV"))
        offspeed_pct = sum(v for k, v in pitch_mix.items() if k in ("CH", "FS", "FO"))
        fastball_pct = sum(v for k, v in pitch_mix.items() if k in ("FF", "SI", "FC", "FT"))
        logger.info("Savant " + str(player_id) + " season=" + str(season) + ": SwStr=" + str(swstr_pct) + " CSW=" + str(csw_pct) + " breaking=" + str(breaking_pct))
        return {
            "swstr_pct": swstr_pct,
            "csw_pct": csw_pct,
            "total_pitches": total_pitches,
            "pitch_mix": pitch_mix,
            "breaking_ball_pct": breaking_pct,
            "offspeed_pct": offspeed_pct,
            "fastball_pct": fastball_pct,
            "season": season,
        }
    except Exception as e:
        logger.error("Savant fetch failed for " + str(player_id) + ": " + str(e))
        return None
 
 
def get_blended_savant_stats(player_id):
    from engine.stats.mlb_stats import get_season_weight
    try:
        current = get_pitcher_savant_stats(player_id, CURRENT_YEAR)
        last = get_pitcher_savant_stats(player_id, LAST_YEAR)
        current_pitches = current.get("total_pitches", 0) if current else 0
        current_starts_estimate = max(1, current_pitches // 85)
        cw, lw = get_season_weight(current_starts_estimate)
        if not current and not last:
            return _neutral_savant()
        if not last:
            cw, lw = 1.0, 0.0
        if not current:
            cw, lw = 0.0, 1.0
        curr_swstr = current.get("swstr_pct", 0.10) if current else 0.10
        last_swstr = last.get("swstr_pct", 0.10) if last else 0.10
        curr_csw = current.get("csw_pct", 0.28) if current else 0.28
        last_csw = last.get("csw_pct", 0.28) if last else 0.28
        curr_breaking = current.get("breaking_ball_pct", 0.25) if current else 0.25
        last_breaking = last.get("breaking_ball_pct", 0.25) if last else 0.25
        blended_swstr = round((curr_swstr * cw) + (last_swstr * lw), 4)
        blended_csw = round((curr_csw * cw) + (last_csw * lw), 4)
        blended_breaking = round((curr_breaking * cw) + (last_breaking * lw), 4)
        logger.info("Blended Savant " + str(player_id) + ": SwStr=" + str(blended_swstr) + " CSW=" + str(blended_csw))
        return {
            "swstr_pct": blended_swstr,
            "csw_pct": blended_csw,
            "breaking_ball_pct": blended_breaking,
            "current_weight": cw,
            "last_season_weight": lw,
        }
    except Exception as e:
        logger.error("Blended Savant failed for " + str(player_id) + ": " + str(e))
        return _neutral_savant()
 
 
def get_swstr_k_adjustment(swstr_pct):
    LEAGUE_AVG_SWSTR = 0.107
    if swstr_pct <= 0:
        return 1.0
    ratio = swstr_pct / LEAGUE_AVG_SWSTR
    adj = 0.70 + (ratio * 0.30)
    adj = max(0.80, min(1.25, adj))
    logger.info("SwStr=" + str(swstr_pct) + " adj=" + str(round(adj, 4)))
    return round(adj, 4)
 
 
def get_pitch_mix_adjustment(breaking_ball_pct):
    LEAGUE_AVG_BREAKING = 0.28
    if breaking_ball_pct > LEAGUE_AVG_BREAKING + 0.08:
        return 1.05
    elif breaking_ball_pct > LEAGUE_AVG_BREAKING + 0.04:
        return 1.02
    elif breaking_ball_pct < LEAGUE_AVG_BREAKING - 0.08:
        return 0.95
    return 1.0
 
 
def _neutral_savant():
    return {
        "swstr_pct": 0.107,
        "csw_pct": 0.280,
        "breaking_ball_pct": 0.280,
        "current_weight": 0.50,
        "last_season_weight": 0.50,
    }
