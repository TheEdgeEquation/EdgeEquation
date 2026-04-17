from core.posting import post_text
from core.formatting import format_domestic_fact
from modes.facts.facts import _load_facts
from core.scheduler_state import get_index

def run():
    # Load all domestic facts
    facts = [f for f in _load_facts() if "domestic" in f["tags"]]

    # Determine which fact to use today
    idx = get_index("fact_domestic") % len(facts)
    raw = facts[idx]["text"]

    # Format the fact
    text = format_domestic_fact(raw)

    # Post it
    post_text(text)

    return text
