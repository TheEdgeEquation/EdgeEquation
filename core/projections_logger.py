# core/projections_logger.py

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

BASE_WAL_DIR = Path("data") / "wal" / "projections"


def _ensure_wal_dir() -> None:
    BASE_WAL_DIR.mkdir(parents=True, exist_ok=True)


def _today_str(ts: Optional[datetime] = None) -> str:
    ts = ts or datetime.utcnow()
    return ts.strftime("%Y-%m-%d")


def log_projection(payload: Dict[str, Any]) -> None:
    """
    Append a single projection record to the daily JSONL WAL file.

    Expected core fields (can include more):
      - projection_id: str
      - timestamp: ISO 8601 string
      - sport: str
      - league: str
      - game_id: str
      - home_team: str
      - away_team: str
      - start_time: ISO 8601 string
      - market: str
      - team: Optional[str]
      - player: Optional[str]
      - side: Optional[str]
      - line: Optional[float]
      - price: Optional[float]
      - model_projection: Optional[float]
      - model_prob: Optional[float]
      - edge_ev: Optional[float]
      - mode: str
      - posted_to_x: bool
    """
    _ensure_wal_dir()

    # Ensure timestamp exists
    if "timestamp" not in payload:
        payload["timestamp"] = datetime.utcnow().isoformat() + "Z"

    # Derive date from timestamp for file naming
    try:
        ts = datetime.fromisoformat(payload["timestamp"].replace("Z", ""))
    except Exception:
        ts = datetime.utcnow()

    date_str = _today_str(ts)
    wal_file = BASE_WAL_DIR / f"{date_str}.jsonl"

    with wal_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
