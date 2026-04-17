from core.posting import post_text
from core.formatting import format_domestic_fact
from core.scheduler_state import get_index
from edge-equation.engines.facts import _load_facts

def run():
    facts = _load_facts()
    domestic = [f for f in facts if "domestic" in f.get("tags", [])]

    if not domestic:
        text = format_domestic_fact("No domestic facts available.")
        post_text(text)
        return text

    idx = get_index("fact_domestic") % len(domestic)
    raw = domestic[idx]["text"]

    text = format_domestic_fact(raw)
    post_text(text)
    return text
