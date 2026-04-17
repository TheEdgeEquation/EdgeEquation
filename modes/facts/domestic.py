from core.posting import post_text
import json
from pathlib import Path
from datetime import datetime

FACTS_PATH = Path("data/facts.json")

def run():
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

    index = datetime.utcnow().timetuple().tm_yday % len(domestic_facts)
    fact = domestic_facts[index]

    text = f"📊 Domestic Fact of the Day\n\n{fact['text']}\n\n#AnalyticsNotFeelings"
    post_text(text)
