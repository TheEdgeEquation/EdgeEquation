# engines/facts.py
import json
from pathlib import Path

from core.twitter_client import post_text
from core.scheduler_state import get_index, bump_index

FACTS_PATH = Path("data/facts.json")


def _load_facts():
    import json
    import os

    path = "data/facts.json"

    if not os.path.exists(path):
        raise FileNotFoundError(f"facts.json not found at {path}")

    with open(path, "r") as f:
        data = json.load(f)

    # If grouped by category (domestic/overseas)
    if isinstance(data, dict):
        combined = []
        for group in data.values():
            if isinstance(group, list):
                combined.extend(group)
        return combined

    # If already a flat list
    return data


    raise ValueError("facts.json is not in a supported format")



def _format_fact(fact: dict) -> str:
    return (
        "Analytical Fact of the Day:\n"
        f"{fact['text']}\n\n"
        "The engine never sleeps.\n"
        f"{fact['hashtags']}"
    )


def post_domestic_fact():
    facts = [f for f in _load_facts() if "domestic" in f["tags"]]
    if not facts:
        return
    idx = get_index("fact_domestic") % len(facts)
    fact = facts[idx]
    post_text(_format_fact(fact))
    bump_index("fact_domestic", len(facts))


def post_overseas_fact():
    facts = [f for f in _load_facts() if "overseas" in f["tags"]]
    if not facts:
        return
    idx = get_index("fact_overseas") % len(facts)
    fact = facts[idx]
    post_text(_format_fact(fact))
    bump_index("fact_overseas", len(facts))
