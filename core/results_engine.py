# core/results_engine.py

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

PROJ_DIR = Path("data") / "wal" / "projections"
RES_DIR = Path("data") / "wal" / "results"


# ---------------------------------------------------------
# 1. LOADERS
# ---------------------------------------------------------

def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def load_projections_for_date(date_str: str) -> List[Dict[str, Any]]:
    file = PROJ_DIR / f"{date_str}.jsonl"
    return load_jsonl(file)


def load_results_for_date(date_str: str) -> List[Dict[str, Any]]:
    file = RES_DIR / f"{date_str}.jsonl"
    return load_jsonl(file)


# ---------------------------------------------------------
# 2. MATCHING LOGIC
# ---------------------------------------------------------

def match_projection_to_result(
    projection: Dict[str, Any],
    results: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Join key: game_id + market + team (if applicable)
    """
    game_id = projection.get("game_id")
    market = projection.get("market")
    team = projection.get("team")

    for r in results:
        if r.get("game_id") != game_id:
            continue

        # ML / spread / total
        if market in ("moneyline", "spread", "total"):
            return r

        # Player props
        if projection.get("player"):
            return r

    return None


# ---------------------------------------------------------
# 3. GRADING LOGIC
# ---------------------------------------------------------

def grade_projection(
    projection: Dict[str, Any],
    result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compute HIT / MISS / PUSH and EV delta.
    """

    market = projection.get("market")
    team = projection.get("team")
    player = projection.get("player")

    home = result.get("home_team")
    away = result.get("away_team")
    hs = result.get("home_score")
    as_ = result.get("away_score")

    # -------------------------------
    # Moneyline grading
    # -------------------------------
    if market == "moneyline":
        winner = away if as_ > hs else home
        hit = (winner == team)
        outcome = "HIT" if hit else "MISS"

        # EV delta (simple version)
        projected_ev = projection.get("edge_ev", 0)
        realized_ev = +1 if hit else -1
        ev_delta = realized_ev - projected_ev

        return {
            "outcome": outcome,
            "ev_delta": ev_delta,
            "final_score": f"{away} {as_} — {home} {hs}"
        }

    # -------------------------------
    # Totals grading
    # -------------------------------
    if market == "total":
        total = hs + as_
        side = projection.get("side")  # over/under
        line = projection.get("line")

        if side == "over":
            if total > line:
                outcome = "HIT"
            elif total == line:
                outcome = "PUSH"
            else:
                outcome = "MISS"
        else:
            if total < line:
                outcome = "HIT"
            elif total == line:
                outcome = "PUSH"
            else:
                outcome = "MISS"

        projected_ev = projection.get("edge_ev", 0)
        realized_ev = 1 if outcome == "HIT" else -1 if outcome == "MISS" else 0
        ev_delta = realized_ev - projected_ev

        return {
            "outcome": outcome,
            "ev_delta": ev_delta,
            "final_score": f"{away} {as_} — {home} {hs}"
        }

    # -------------------------------
    # Player props grading
    # -------------------------------
    if player:
        stat_name = projection.get("market").replace("player_", "")
        line = projection.get("line")
        side = projection.get("side")

        # Find player stat
        stat_val = None
        for p in result.get("player_stats", []):
            if p.get("player") == player:
                stat_val = p.get(stat_name)
                break

        if stat_val is None:
            return {
                "outcome": "NO_DATA",
                "ev_delta": 0,
                "final_score": "N/A"
            }

        if side == "over":
            if stat_val > line:
                outcome = "HIT"
            elif stat_val == line:
                outcome = "PUSH"
            else:
                outcome = "MISS"
        else:
            if stat_val < line:
                outcome = "HIT"
            elif stat_val == line:
                outcome = "PUSH"
            else:
                outcome = "MISS"

        projected_ev = projection.get("edge_ev", 0)
        realized_ev = 1 if outcome == "HIT" else -1 if outcome == "MISS" else 0
        ev_delta = realized_ev - projected_ev

        return {
            "outcome": outcome,
            "ev_delta": ev_delta,
            "final_score": f"{player}: {stat_val} {stat_name}"
        }

    # Default fallback
    return {
        "outcome": "UNSUPPORTED",
        "ev_delta": 0,
        "final_score": "N/A"
    }


# ---------------------------------------------------------
# 4. BUILD RESULTS PAYLOAD
# ---------------------------------------------------------

def build_results_payload(date_str: str) -> Dict[str, Any]:
    projections = load_projections_for_date(date_str)
    results = load_results_for_date(date_str)

    graded = []
    correct = 0
    total = 0
    ev_total = 0

    for p in projections:
        r = match_projection_to_result(p, results)
        if not r:
            continue

        g = grade_projection(p, r)

        total += 1
        if g["outcome"] == "HIT":
            correct += 1

        ev_total += g["ev_delta"]

        graded.append({
            "label": p.get("projection_id"),
            "outcome": g["outcome"],
            "key_metric": f"Model Prob: {p.get('model_prob')}",
            "context": f"{p.get('sport')} {p.get('market')}",
            "model_signal": f"EV: {p.get('edge_ev')}",
            "trend": "N/A",
            "matchup_delta": "N/A",
            "historical_comp": "N/A",
            "final_score": g["final_score"]
        })

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "results": graded,
        "totals": {
            "correct": correct,
            "total": total,
            "ev_delta": round(ev_total, 2)
        }
    }
