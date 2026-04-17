from core.posting import post_text
import json
from pathlib import Path
from datetime import datetime

FACTS_PATH = Path("data/facts.json")

def run():
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

    index = datetime.utcnow().timetuple().tm_yday % len(overseas_facts)
    fact = overseas_facts[index]

    text = f"🌍 Overseas Fact of the Day\n\n{fact['text']}\n\n#AnalyticsNotFeelings"
    post_text(text)
