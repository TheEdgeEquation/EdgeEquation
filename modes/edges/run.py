# modes/edges/run.py
"""
Edges Board Engine
The Edge Equation — Facts. Not Feelings.
"""

from core.posting import post_text
from core.formatting import format_edges_block
from core.data_loader import load_edges
from core.utils import now_timestamp


def run():
    edges = load_edges()

    payload = {
        "timestamp": now_timestamp(),
        "edges": edges,
    }

    text = format_edges_block(payload)
    post_text(text, mode="edges", payload=payload)
