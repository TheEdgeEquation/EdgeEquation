# core/scheduler_state.py
import json
from pathlib import Path

STATE_PATH = Path("data/state.json")


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text())


def save_state(state: dict):
    STATE_PATH.write_text(json.dumps(state, indent=2))


def get_index(key: str) -> int:
    state = load_state()
    return state.get(key, 0)


def bump_index(key: str, max_len: int) -> int:
    state = load_state()
    idx = state.get(key, 0)
    idx = (idx + 1) % max_len
    state[key] = idx
    save_state(state)
    return idx
