# modes/results/run.py
"""
Results Mode Engine
The Edge Equation — Facts. Not Feelings.
"""

from core.posting import post_text
from core.formatting import format_results_block
from core.data_loader import load_results  # should return {date, results, summary}


def run():
    payload = load_results()
    text = format_results_block(payload)
    post_text(text, mode="results", payload=payload)
