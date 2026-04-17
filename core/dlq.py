# core/dlq.py

import os
from datetime import datetime

DLQ_DIR = "dlq"

# Ensure directory exists
os.makedirs(DLQ_DIR, exist_ok=True)


def write_dlq(text: str, mode: str, error: str):
    """
    Writes a DLQ entry for failed posts.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    filename = f"{timestamp.replace(':', '_')}_{mode}.dlq"
    path = os.path.join(DLQ_DIR, filename)

    payload = {
        "mode": mode,
        "timestamp": timestamp,
        "error": error,
        "text": text,
    }

    with open(path, "w") as f:
        f.write(str(payload))
