# modes/facts/run.py
"""
Facts Mode Engine
The Edge Equation — Facts. Not Feelings.
"""

from core.posting import post_text
from core.formatting import format_facts_block
from core.data_loader import load_facts
from core.utils import now_timestamp


def run():
    facts = load_facts()

    payload = {
        "timestamp": now_timestamp(),
        "facts": facts,
    }

    text = format_facts_block(payload)
    post_text(text, mode="facts", payload=payload)
