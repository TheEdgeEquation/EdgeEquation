"""
Watchdog — Monitors pipeline health and posts alerts on failures.
Runs after each phase to verify output integrity.
"""
import os
import json
from datetime import datetime


class Watchdog:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        self.log_path = os.path.join(cache_dir, "watchdog.json")
        os.makedirs(cache_dir, exist_ok=True)

    def _load_log(self):
        if os.path.exists(self.log_path):
            with open(self.log_path, "r") as f:
                return json.load(f)
        return {"events": []}

    def _save_log(self, data):
        with open(self.log_path, "w") as f:
            json.dump(data, f, indent=2)

    def log_event(self, phase, status, message="", details=None):
        log = self._load_log()
        event = {
            "phase": phase,
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        }
        log["events"].append(event)
        self._save_log(log)
        return event
