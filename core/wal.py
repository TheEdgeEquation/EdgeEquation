# core/wal.py

import os
import uuid
from datetime import datetime

WAL_DIR = "wal"

# Ensure directory exists
os.makedirs(WAL_DIR, exist_ok=True)


def write_wal(text: str, mode: str) -> str:
    """
    Writes a WAL entry and returns its ID.
    """
    wal_id = str(uuid.uuid4())
    path = os.path.join(WAL_DIR, f"{wal_id}.wal")

    payload = {
        "id": wal_id,
        "mode": mode,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "text": text,
    }

    with open(path, "w") as f:
        f.write(str(payload))

    return wal_id


def clear_wal(wal_id: str):
    """
    Removes a WAL entry after successful posting.
    """
    path = os.path.join(WAL_DIR, f"{wal_id}.wal")
    if os.path.exists(path):
        os.remove(path)
