# modes/facts/domestic.py

import json
from pathlib import Path

FACTS_PATH = Path("data/facts.json")

def run():
    """
    Domestic Fact of the Day (7:30 AM CT)
    Pulls from IDs 1–60.
    Placeholder-safe: prints the fact instead of posting.
    """
    print("Running Domestic Fact Mode")

    if not FACTS_PATH.exists():
        print("ERROR: facts.json not found.")
        return

    with open(FACTS_PATH, "r", encoding="utf-8") as f:
        facts = json.load(f)

    domestic_facts = [f for f in facts if 1 <= f["id"] <= 60]

    if not domestic_facts:
        print("ERROR: No domestic facts found.")
        return

    # Deterministic selection: rotate based on day of year
    from datetime import datetime
    index = datetime.utcnow().timetuple().tm_yday % len(domestic_facts)
    fact = domestic_facts[index]

    print(f"Selected Domestic Fact ID {fact['id']}:")
    print(fact["text"])
