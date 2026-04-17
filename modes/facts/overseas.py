# modes/facts/overseas.py

import json
from pathlib import Path

FACTS_PATH = Path("data/facts.json")

def run():
    """
    Overseas Fact of the Day (1:00 AM CT)
    Pulls from IDs 61–120.
    Placeholder-safe: prints the fact instead of posting.
    """
    print("Running Overseas Fact Mode")

    if not FACTS_PATH.exists():
        print("ERROR: facts.json not found.")
        return

    with open(FACTS_PATH, "r", encoding="utf-8") as f:
        facts = json.load(f)

    overseas_facts = [f for f in facts if 61 <= f["id"] <= 120]

    if not overseas_facts:
        print("ERROR: No overseas facts found.")
        return

    # Deterministic selection: rotate based on day of year
    from datetime import datetime
    index = datetime.utcnow().timetuple().tm_yday % len(overseas_facts)
    fact = overseas_facts[index]

    print(f"Selected Overseas Fact ID {fact['id']}:")
    print(fact["text"])
