# engines/edges.py
from core.twitter_client import post_text


def _fetch_valid_edges(window: str) -> list[dict]:
    """
    Placeholder edge fetcher.
    Later this will:
    - read your model output
    - filter by game not started
    - filter by confidence threshold
    - filter by odds availability
    - return formatted edges
    """
    return []  # empty list = no posts (safe default)


def _format_edge(edge: dict) -> str:
    return edge["formatted_text"]


def post_morning_edges():
    edges = _fetch_valid_edges("morning")
    for edge in edges:
        post_text(_format_edge(edge))


def post_evening_edges():
    edges = _fetch_valid_edges("evening")
    for edge in edges:
        post_text(_format_edge(edge))
    

