"""
Edge Equation — Results Tracker
Private data store. Stores everything — posted or not.
Tracks ML, spread, and total accuracy for model tuning.
Never posted publicly. Email only for internal review.
"""
 
import json
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
 
logger = logging.getLogger(__name__)
 
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "results")
 
 
def _ensure_dir():
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
 
 
def _results_file(date_str: str = None) -> str:
    if not date_str:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return os.path.join(DATA_DIR, f"{date_str}_results.json")
 
 
def load_results(date_str: str = None) -> list:
    """Load results for a given date."""
    _ensure_dir()
    path = _results_file(date_str)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Results load failed: {e}")
        return []
 
 
def save_results(entries: list, date_str: str = None) -> bool:
    """Save results to disk."""
    _ensure_dir()
    path = _results_file(date_str)
    try:
        with open(path, "w") as f:
            json.dump(entries, f, indent=2)
        logger.info(f"Results saved: {len(entries)} entries → {path}")
        return True
    except Exception as e:
        logger.error(f"Results save failed: {e}")
        return False
 
 
def store_game(
    sport: str,
    teams: str,
    proj_score: str,
    proj_total: str,
    vegas_total: str,
    vegas_moneyline: str = "",
    vegas_spread: str = "",
    edge_total: str = "",
    edge_moneyline: str = "",
    edge_spread: str = "",
    actual_score: str = "",
    actual_total: str = "",
    public_posted: bool = False,
    edge_rank: int = 0,
    date_str: str = None,
) -> dict:
    """Store a game projection entry."""
    entry = {
        "type": "game",
        "sport": sport,
        "teams": teams,
        "proj_score": proj_score,
        "proj_total": proj_total,
        "vegas_total": vegas_total,
        "vegas_moneyline": vegas_moneyline,
        "vegas_spread": vegas_spread,
        "edge_total": edge_total,
        "edge_moneyline": edge_moneyline,
        "edge_spread": edge_spread,
        "actual_score": actual_score,
        "actual_total": actual_total,
        "win_loss_total": "",
        "win_loss_moneyline": "",
        "win_loss_spread": "",
        "edge_rank": str(edge_rank),
        "public_posted": str(public_posted).lower(),
        "internal_grade": "",
        "stored_at": datetime.now(timezone.utc).isoformat(),
    }
 
    # Calculate results if we have actuals
    if actual_total and proj_total and vegas_total:
        entry = _calculate_results(entry)
 
    # Append to daily results
    existing = load_results(date_str)
    existing.append(entry)
    save_results(existing, date_str)
 
    return entry
 
 
def store_prop(
    sport: str,
    player: str,
    prop: str,
    proj_value: str,
    vegas_line: str,
    edge_percent: str = "",
    actual_result: str = "",
    public_posted: bool = False,
    edge_rank: int = 0,
    date_str: str = None,
) -> dict:
    """Store a prop projection entry."""
    entry = {
        "type": "prop",
        "sport": sport,
        "teams_or_player": player,
        "prop": prop,
        "proj_value": proj_value,
        "vegas_line": vegas_line,
        "edge_percent": edge_percent,
        "actual_result": actual_result,
        "win_loss": "",
        "edge_rank": str(edge_rank),
        "public_posted": str(public_posted).lower(),
        "internal_grade": _calculate_grade(edge_percent),
        "stored_at": datetime.now(timezone.utc).isoformat(),
    }
 
    if actual_result and proj_value and vegas_line:
        entry = _calculate_prop_result(entry)
 
    existing = load_results(date_str)
    existing.append(entry)
    save_results(existing, date_str)
 
    return entry
 
 
def update_actuals(teams: str, actual_score: str, actual_total: str,
                   date_str: str = None) -> bool:
    """Update actual results for a stored game."""
    existing = load_results(date_str)
    updated = False
    for entry in existing:
        if entry.get("teams") == teams and entry.get("type") == "game":
            entry["actual_score"] = actual_score
            entry["actual_total"] = actual_total
            entry = _calculate_results(entry)
            updated = True
            logger.info(f"Updated actuals for {teams}: {actual_score} (total: {actual_total})")
    if updated:
        save_results(existing, date_str)
    return updated
 
 
def _calculate_results(entry: dict) -> dict:
    """Calculate win/loss for total, ML, and spread."""
    try:
        proj_total = float(entry.get("proj_total", 0))
        vegas_total = float(entry.get("vegas_total", 0))
        actual_total = float(entry.get("actual_total", 0))
 
        # Total: if proj > vegas we're on OVER
        if proj_total > vegas_total:
            entry["win_loss_total"] = "WIN" if actual_total > vegas_total else "LOSS"
        else:
            entry["win_loss_total"] = "WIN" if actual_total < vegas_total else "LOSS"
 
        # Internal grade
        edge = entry.get("edge_total", "0").replace("%", "")
        entry["internal_grade"] = _calculate_grade(edge + "%")
 
    except Exception as e:
        logger.warning(f"Result calculation failed: {e}")
 
    return entry
 
 
def _calculate_prop_result(entry: dict) -> dict:
    """Calculate win/loss for a prop."""
    try:
        proj = float(entry.get("proj_value", 0))
        line = float(entry.get("vegas_line", 0))
        actual = float(entry.get("actual_result", 0))
 
        # If proj > line we're on the OVER
        if proj > line:
            entry["win_loss"] = "WIN" if actual > line else "LOSS"
        else:
            entry["win_loss"] = "WIN" if actual < line else "LOSS"
 
    except Exception as e:
        logger.warning(f"Prop result calculation failed: {e}")
 
    return entry
 
 
def _calculate_grade(edge_percent: str) -> str:
    """Internal grade based on edge % — never shown publicly in Phase 1."""
    try:
        edge = float(str(edge_percent).replace("%", "").strip())
        if edge >= 15:
            return "A+"
        elif edge >= 10:
            return "A"
        elif edge >= 5:
            return "A-"
        else:
            return "B"
    except Exception:
        return "N/A"
 
 
def build_daily_summary(date_str: str = None) -> dict:
    """Build daily accuracy summary for email."""
    entries = load_results(date_str)
    if not entries:
        return {"total": 0, "wins": 0, "losses": 0, "accuracy": 0.0}
 
    games = [e for e in entries if e.get("type") == "game" and e.get("win_loss_total")]
    props = [e for e in entries if e.get("type") == "prop" and e.get("win_loss")]
    public = [e for e in entries if e.get("public_posted") == "true"]
 
    def calc_record(items, key):
        wins = sum(1 for i in items if i.get(key) == "WIN")
        losses = sum(1 for i in items if i.get(key) == "LOSS")
        total = wins + losses
        acc = round(wins / total * 100, 1) if total > 0 else 0
        return {"wins": wins, "losses": losses, "total": total, "accuracy": acc}
 
    return {
        "date": date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "games": calc_record(games, "win_loss_total"),
        "props": calc_record(props, "win_loss"),
        "public": calc_record(public, "win_loss_total"),
        "total_entries": len(entries),
        "public_posted": len(public),
    }
 
 
def build_ytd_summary() -> dict:
    """Build year-to-date summary across all stored results."""
    _ensure_dir()
    all_entries = []
    try:
        for f in sorted(Path(DATA_DIR).glob("*_results.json")):
            with open(f) as file:
                all_entries.extend(json.load(file))
    except Exception as e:
        logger.warning(f"YTD build failed: {e}")
        return {}
 
    games = [e for e in all_entries if e.get("type") == "game" and e.get("win_loss_total")]
    props = [e for e in all_entries if e.get("type") == "prop" and e.get("win_loss")]
 
    def calc(items, key):
        wins = sum(1 for i in items if i.get(key) == "WIN")
        losses = sum(1 for i in items if i.get(key) == "LOSS")
        total = wins + losses
        acc = round(wins / total * 100, 1) if total > 0 else 0
        return f"{wins}-{losses} ({acc}%)"
 
    return {
        "games_record": calc(games, "win_loss_total"),
        "props_record": calc(props, "win_loss"),
        "total_entries": len(all_entries),
    }
 
 
if __name__ == "__main__":
    # Test
    store_game(
        sport="MLB",
        teams="Yankees @ Red Sox",
        proj_score="4.3 - 5.6",
        proj_total="9.9",
        vegas_total="8.5",
        vegas_moneyline="-135",
        vegas_spread="-1.5",
        edge_total="16.5%",
        public_posted=True,
        edge_rank=1,
    )
    print("Stored game.")
    summary = build_daily_summary()
    print("Summary:", json.dumps(summary, indent=2))
