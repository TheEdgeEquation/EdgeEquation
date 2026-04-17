# engines/facts.py
import json
from pathlib import Path

from core.twitter_client import post_text
from core.scheduler_state import get_index, bump_index

FACTS_PATH = Path("data/facts.json")


def _load_facts() -> list[dict]:
    return json.loads(FACTS_PATH.read_text())


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
