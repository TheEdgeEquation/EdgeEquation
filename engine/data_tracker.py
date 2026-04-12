import os
import json
import logging
from datetime import datetime, timedelta
from config.settings import DATA_DIR

logger = logging.getLogger(__name__)


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _daily_path(date_str: str, prefix: str = "plays") -> str:
    return os.path.join(DATA_DIR, f"{prefix}_{date_str}.json")


def save_plays(plays: list[dict], style: str = "ee") -> str:
    _ensure_data_dir()
    date_str = datetime.now().strftime("%Y%m%d")
    path = _daily_path(date_str, f"{style}_plays")
    payload = {
        "date": date_str,
        "style": style,
        "generated_at": datetime.now().isoformat(),
        "plays": plays,
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    logger.info(f"Plays saved: {path}")
    return path


def load_plays(date_str: str | None = None, style: str = "ee") -> list[dict]:
    if not date_str:
        date_str = datetime.now().strftime("%Y%m%d")
    path = _daily_path(date_str, f"{style}_plays")
    if not os.path.exists(path):
        logger.warning(f"No plays file found: {path}")
        return []
    with open(path) as f:
        data = json.load(f)
    return data.get("plays", [])


def save_results(results: list[dict], style: str = "ee") -> str:
    _ensure_data_dir()
    date_str = datetime.now().strftime("%Y%m%d")
    path = _daily_path(date_str, f"{style}_results")
    hits = sum(1 for r in results if r.get("hit"))
    payload = {
        "date": date_str,
        "style": style,
        "saved_at": datetime.now().isoformat(),
        "record": f"{hits}-{len(results) - hits}",
        "results": results,
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    logger.info(f"Results saved: {path}")
    return path


def load_results(date_str: str | None = None, style: str = "ee") -> list[dict]:
    if not date_str:
        date_str = datetime.now().strftime("%Y%m%d")
    path = _daily_path(date_str, f"{style}_results")
    if not os.path.exists(path):
        logger.warning(f"No results file for {date_str}")
        return []
    with open(path) as f:
        data = json.load(f)
    return data.get("results", [])


def build_weekly_stats(style: str = "ee") -> dict:
    today = datetime.now()
    total, hits, misses = 0, 0, 0
    best_play, worst_play = None, None
    best_edge, worst_edge = -1, 999
    for i in range(7):
        day = today - timedelta(days=i)
        date_str = day.strftime("%Y%m%d")
        results = load_results(date_str, style)
        for r in results:
            total += 1
            if r.get("hit"):
                hits += 1
                if r.get("edge", 0) > best_edge:
                    best_edge = r["edge"]
                    best_play = f"{r['player']} {r['display_line']} {r['prop_label']} ✓"
            else:
                misses += 1
                if r.get("edge", 999) < worst_edge:
                    worst_edge = r.get("edge", 0)
                    worst_play = f"{r['player']} {r['display_line']} {r['prop_label']} ✗"
    win_rate = (hits / total * 100) if total else 0
    units = round(hits * 0.91 - misses * 1.0, 2)
    week_start = (today - timedelta(days=6)).strftime("%b %d")
    week_end = today.strftime("%b %d, %Y")
    return {
        "total": total,
        "hits": hits,
        "misses": misses,
        "win_rate": round(win_rate, 1),
        "units": units,
        "best_play": best_play or "N/A",
        "worst_play": worst_play or "N/A",
        "week_label":
