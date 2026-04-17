from core.posting import post_text
from core.formatting import format_edges_evening
from engines.edges import get_evening_edges

def run():
    body = get_evening_edges()
    text = format_edges_evening(body)
    post_text(text)
    return text
