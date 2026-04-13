import json
import os
import logging
from datetime import datetime, timedelta
 
logger = logging.getLogger(__name__)
 
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
 
 
def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
 
 
def _plays_file(date_str, style="ee"):
    return os.path.join(DATA_DIR, style + "_plays_" + date_str + ".json")
 
 
def _results_file(date_str, style="ee"):
    return os.path.join(DATA_DIR, style + "_results_" + date_str + ".json")
 
 
def _history_file(style="ee"):
    return os.path.join(DATA_DIR, style + "_history.json")
 
 
def save_plays(plays, style="ee"):
    _ensure_dir()
    date_str = datetime.now().strftime("%Y%m%d")
    path = _plays_file(date_str, style)
    try:
        with open(path, "w") as f:
            json.dump(plays, f, indent=2)
        logger.info("Plays saved: " + path)
    except Exception as e:
        logger.error("Save plays failed: " + str(e))
 
 
def load_plays(date_str, style="ee"):
    path = _plays_file(date_str, style)
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error("Load plays failed: " + str(e))
    return []
 
 
def save_results(results, style="ee"):
    _ensure_dir()
    date_str = datetime.now().strftime("%Y%m%d")
    path = _results_file(date_str, style)
    try:
        with open(path, "w") as f:
            json.dump(results, f, indent=2)
        _update_history(results, style)
        logger.info("Results saved: " + path)
    except Exception as e:
        logger.error("Save results failed: " + str(e))
 
 
def load_results(date_str, style="ee"):
    path = _results_file(date_str, style)
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error("Load results failed: " + str(e))
    return []
 
 
def _update_history(results, style="ee"):
    path = _history_file(style)
    try:
        history = []
        if os.path.exists(path):
            with open(path, "r") as f:
                history = json.load(f)
        date_str = datetime.now().strftime("%Y%m%d")
        for r in results:
            entry = {
                "date": date_str,
                "player": r.get("player", ""),
                "sport": r.get("sport", ""),
                "prop_label": r.get("prop_label", ""),
                "line": r.get("line", 0),
                "display_line": r.get("display_line", ""),
                "display_odds": r.get("display_odds", ""),
                "grade": r.get("grade", ""),
                "edge": r.get("edge", 0),
                "true_lambda": r.get("true_lambda", 0),
                "confidence_score": r.get("confidence_score", 0),
                "won": r.get("won", None),
                "actual_result": r.get("actual_result", None),
                "result_checked": r.get("result_checked", False),
                "recommended_units": r.get("recommended_units", 0.5),
                "closing_line": r.get("closing_line", None),
                "clv": r.get("clv", None),
                "style": style,
            }
            history.append(entry)
        with open(path, "w") as f:
            json.dump(history, f, indent=2)
        logger.info("History updated: " + str(len(history)) + " total entries")
    except Exception as e:
        logger.error("History update failed: " + str(e))
 
 
def build_weekly_stats(style="ee"):
    path = _history_file(style)
    try:
        if not os.path.exists(path):
            return _empty_stats()
        with open(path, "r") as f:
            history = json.load(f)
        cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
        week = [h for h in history if h.get("date", "") >= cutoff and h.get("result_checked")]
        return _calculate_stats(week)
    except Exception as e:
        logger.error("Weekly stats failed: " + str(e))
        return _empty_stats()
 
 
def build_all_time_stats(style="ee"):
    path = _history_file(style)
    try:
        if not os.path.exists(path):
            return _empty_stats()
        with open(path, "r") as f:
            history = json.load(f)
        checked = [h for h in history if h.get("result_checked")]
        return _calculate_stats(checked)
    except Exception as e:
        logger.error("All time stats failed: " + str(e))
        return _empty_stats()
 
 
def _calculate_stats(plays):
    if not plays:
        return _empty_stats()
    total = len(plays)
    wins = sum(1 for p in plays if p.get("won"))
    losses = total - wins
    win_rate = round(wins / total * 100, 1) if total > 0 else 0
    total_units_wagered = sum(p.get("recommended_units", 0.5) for p in plays)
    total_units_won = 0
    for p in plays:
        if p.get("won"):
            units = p.get("recommended_units", 0.5)
            odds_str = str(p.get("display_odds", "-115")).replace("+", "")
            try:
                odds = int(odds_str)
                if odds > 0:
                    total_units_won += units * odds / 100.0
                else:
                    total_units_won += units * 100.0 / abs(odds)
            except Exception:
                total_units_won += units * 0.91
    total_units_lost = sum(p.get("recommended_units", 0.5) for p in plays if not p.get("won"))
    net_units = round(total_units_won - total_units_lost, 2)
    roi = round(net_units / total_units_wagered * 100, 1) if total_units_wagered > 0 else 0
    by_grade = {}
    for grade in ("A+", "A", "A-"):
        grade_plays = [p for p in plays if p.get("grade") == grade]
        grade_wins = sum(1 for p in grade_plays if p.get("won"))
        by_grade[grade] = {"wins": grade_wins, "total": len(grade_plays), "win_rate": round(grade_wins / len(grade_plays) * 100, 1) if grade_plays else 0}
    by_sport = {}
    for sport in ("baseball_mlb", "basketball_nba", "icehockey_nhl", "americanfootball_nfl"):
        sport_plays = [p for p in plays if p.get("sport") == sport]
        sport_wins = sum(1 for p in sport_plays if p.get("won"))
        label = sport.split("_")[1].upper() if "_" in sport else sport.upper()
        by_sport[label] = {"wins": sport_wins, "total": len(sport_plays), "win_rate": round(sport_wins / len(sport_plays) * 100, 1) if sport_plays else 0}
    clv_plays = [p for p in plays if p.get("clv") is not None]
    avg_clv = round(sum(p["clv"] for p in clv_plays) / len(clv_plays) * 100, 1) if clv_plays else 0
    lambda_plays = [p for p in plays if p.get("true_lambda") and p.get("actual_result") is not None]
    model_accuracy = 0
    if lambda_plays:
        errors = [abs(p["true_lambda"] - p["actual_result"]) for p in lambda_plays]
        model_accuracy = round(sum(errors) / len(errors), 2)
    return {
        "total": total, "wins": wins, "losses": losses, "win_rate": win_rate,
        "net_units": net_units, "roi": roi, "total_wagered": round(total_units_wagered, 1),
        "by_grade": by_grade, "by_sport": by_sport,
        "avg_clv": avg_clv, "model_accuracy": model_accuracy,
    }
 
 
def _empty_stats():
    return {
        "total": 0, "wins": 0, "losses": 0, "win_rate": 0,
        "net_units": 0, "roi": 0, "total_wagered": 0,
        "by_grade": {"A+": {"wins": 0, "total": 0, "win_rate": 0}, "A": {"wins": 0, "total": 0, "win_rate": 0}, "A-": {"wins": 0, "total": 0, "win_rate": 0}},
        "by_sport": {},
        "avg_clv": 0, "model_accuracy": 0,
    }
