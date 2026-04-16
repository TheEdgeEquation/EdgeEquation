import requests
import logging
from datetime import datetime

logger = logging.getLogger("prizepicks")

PP_API = "https://api.prizepicks.com/projections"

# ------------------------------------------------------------
# 3.0 — CLEAN LABEL MAP
# ------------------------------------------------------------

LABEL_MAP = {
    "Pitcher Strikeouts": "K",
    "Shots on Goal": "SOG",
    "3-PT Made": "3PM",
    "Points": "PTS",
    "Assists": "AST",
    "Rebounds": "REB",
    "Runs": "RUNS",
    "Hits": "HITS",
    "Bases": "TB",
    "Fantasy Score": "FS",
}

# ------------------------------------------------------------
# 3.0 — VALIDATION HELPERS
# ------------------------------------------------------------

def _normalize_label(label):
    return LABEL_MAP.get(label, None)

def _validate_pp_line(pp_line):
    try:
        return float(pp_line)
    except:
        return None

def _validate_market(entry):
    """
    Ensures the PP entry is usable.
    """
    if "projection" not in entry:
        return False
    if "line_score" not in entry["projection"]:
        return False
    if entry["projection"]["line_score"] is None:
        return False
    return True

def _validate_player(entry):
    if "new_player" not in entry:
        return False
    if not entry["new_player"].get("name"):
        return False
    return True

def _validate_stat(entry):
    stat = entry["projection"].get("stat_type")
    return stat in LABEL_MAP

# ------------------------------------------------------------
# 3.0 — MAIN SCRAPER
# ------------------------------------------------------------

def fetch_prizepicks_props():
    """
    Returns a clean, validated list of PrizePicks props.
    Removes:
    - off-board props
    - invalid props
    - mislabeled props
    - props with missing lines
    - props with non-numeric lines
    """

    logger.info("Fetching PrizePicks board...")

    try:
        r = requests.get(PP_API, timeout=10)
        data = r.json()
    except Exception as e:
        logger.error(f"PrizePicks API failed: {e}")
        return []

    raw = data.get("data", [])
    clean_props = []

    for entry in raw:
        try:
            if not _validate_market(entry):
                continue
            if not _validate_player(entry):
                continue
            if not _validate_stat(entry):
                continue

            player = entry["new_player"]["name"]
            stat = entry["projection"]["stat_type"]
            label = _normalize_label(stat)
            line = _validate_pp_line(entry["projection"]["line_score"])

            if label is None:
                continue
            if line is None:
                continue

            clean_props.append({
                "player": player,
                "prop_label": label,
                "line": line,
                "market": stat,
                "pp_id": entry.get("id"),
                "timestamp": datetime.utcnow().isoformat(),
            })

        except Exception as e:
            logger.error(f"Error parsing PP entry: {e}")
            continue

    logger.info(f"PrizePicks: {len(clean_props)} validated props loaded")
    return clean_props
