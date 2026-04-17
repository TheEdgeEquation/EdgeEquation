# core/posting.py

import os
import json
import time
import random
from datetime import datetime
from typing import Optional, Dict, Any

from core.x_client import get_x_client


# ---------- Paths for durability ----------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "..", "data", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

WAL_PATH = os.path.join(LOG_DIR, "posting_wal.jsonl")
DLQ_PATH = os.path.join(LOG_DIR, "posting_dlq.jsonl")
ANALYTICS_PATH = os.path.join(LOG_DIR, "posting_analytics.jsonl")


# ---------- Core logging ----------

def _log(message: str):
    """Simple internal logger."""
    print(f"[POSTING] {message}")


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


# ---------- File helpers ----------

def _append_json_line(path: str, record: Dict[str, Any]):
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        _log(f"ERROR writing to {path}: {e}")


# ---------- Write-Ahead Log (WAL) ----------

def _wal_log_post(kind: str, payload: Dict[str, Any]) -> str:
    """
    Log intent to post before sending.
    Returns a wal_id used to mark completion or DLQ.
    """
    wal_id = f"{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
    record = {
        "wal_id": wal_id,
        "timestamp": _now_iso(),
        "kind": kind,  # "text" or "graphic"
        "payload": payload,
        "status": "pending",
    }
    _append_json_line(WAL_PATH, record)
    return wal_id


def _wal_mark_result(wal_id: str, status: str, extra: Optional[Dict[str, Any]] = None):
    """
    Append a result record for a given wal_id.
    WAL is append-only; we track state via separate records.
    """
    record = {
        "wal_id": wal_id,
        "timestamp": _now_iso(),
        "status": status,  # "success" or "failed"
    }
    if extra:
        record.update(extra)
    _append_json_line(WAL_PATH, record)


# ---------- Dead-Letter Queue (DLQ) ----------

def _dlq_store(kind: str, payload: Dict[str, Any], error_text: str):
    """
    Store permanently failed posts for later replay / inspection.
    """
    record = {
        "timestamp": _now_iso(),
        "kind": kind,
        "payload": payload,
        "error": error_text,
    }
    _append_json_line(DLQ_PATH, record)
    _log(f"Post moved to DLQ ({kind})")


# ---------- Analytics callback ----------

def _analytics_log(kind: str, payload: Dict[str, Any], meta: Dict[str, Any]):
    """
    Log successful posts for analytics and audit.
    """
    record = {
        "timestamp": _now_iso(),
        "kind": kind,
        "payload": payload,
        "meta": meta,
    }
    _append_json_line(ANALYTICS_PATH, record)


# ---------- Retry logic ----------

def _retry(func, max_attempts=6, base_delay=2, max_delay=20, final_wait=15):
    """
    Maximum-resilience retry logic with:
    - Exponential backoff
    - Jitter (randomized delay)
    - Transient error detection
    - Final fallback wait before failing
    """
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            return func()

        except Exception as e:
            last_error = e
            error_text = str(e)

            transient = (
                "503" in error_text or
                "Over capacity" in error_text or
                "Service Unavailable" in error_text or
                "Connection aborted" in error_text or
                "timed out" in error_text or
                "EOF occurred" in error_text or
                "RemoteDisconnected" in error_text
            )

            if not transient:
                raise

            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            jitter = random.uniform(0.5, 1.5)
            sleep_time = delay * jitter

            _log(f"Transient error detected: {error_text}")
            _log(f"Retry {attempt}/{max_attempts} — sleeping {sleep_time:.2f}s")

            time.sleep(sleep_time)

    _log(f"Final wait {final_wait}s before giving up…")
    time.sleep(final_wait)

    raise Exception(f"Max retries reached for posting: {last_error}")


# ---------- Public posting API ----------

def post_text(text: str):
    """
    Unified text posting function.
    All automated modes call this.
    Durability:
      - WAL logs intent
      - Retry on transient failures
      - DLQ on final failure
      - Analytics on success
    """
    _log("Preparing text post")

    if not text or not text.strip():
        _log("ERROR: Empty text passed to post_text()")
        return

    payload = {
        "text": text,
    }

    wal_id = _wal_log_post("text", payload)
    client = get_x_client()

    try:
        result = _retry(lambda: client.update_status(text))
        _wal_mark_result(wal_id, "success", {"result_id": getattr(result, "id", None)})
        _analytics_log(
            "text",
            payload,
            {
                "result_id": getattr(result, "id", None),
                "length": len(text),
            },
        )
        _log("Text post sent successfully")
    except Exception as e:
        error_text = str(e)
        _wal_mark_result(wal_id, "failed", {"error": error_text})
        _dlq_store("text", payload, error_text)
        _log(f"ERROR posting text: {error_text}")


def post_graphic(text: str, image_path: str):
    """
    Unified graphic posting function.
    Manual graphic modes call this.
    Durability:
      - WAL logs intent
      - Retry on transient failures
      - DLQ on final failure
      - Analytics on success
    """
    _log("Preparing graphic post")

    if not text or not text.strip():
        _log("ERROR: Empty text passed to post_graphic()")
        return

    payload = {
        "text": text,
        "image_path": image_path,
    }

    wal_id = _wal_log_post("graphic", payload)
    client = get_x_client()

    try:
        media = _retry(lambda: client.media_upload(image_path))
        result = _retry(lambda: client.update_status(status=text, media_ids=[media.media_id]))
        _wal_mark_result(
            wal_id,
            "success",
            {
                "result_id": getattr(result, "id", None),
                "media_id": getattr(media, "media_id", None),
            },
        )
        _analytics_log(
            "graphic",
            payload,
            {
                "result_id": getattr(result, "id", None),
                "media_id": getattr(media, "media_id", None),
                "length": len(text),
            },
        )
        _log("Graphic post sent successfully")
    except Exception as e:
        error_text = str(e)
        _wal_mark_result(wal_id, "failed", {"error": error_text})
        _dlq_store("graphic", payload, error_text)
        _log(f"ERROR posting graphic: {error_text}")
