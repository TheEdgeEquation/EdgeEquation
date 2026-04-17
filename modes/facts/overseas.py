from core.posting import post_text
from core.formatting import format_overseas_fact
from core.scheduler_state import get_index
from edge_equation.engines.facts import _load_facts

def run():
    # Load all facts from JSON
    facts = _load_facts()

    # Filter for overseas facts
    overseas = [f for f in facts if "overseas" in f.get("tags", [])]

    if not overseas:
        text = format_overseas_fact("No overseas facts available.")
        post_text(text)
        return text

    # Deterministic rotation
    idx = get_index("fact_overseas") % len(overseas)
    raw = overseas[idx]["text"]

    # Format + post
    text = format_overseas_fact(raw)
    post_text(text)
    return text
