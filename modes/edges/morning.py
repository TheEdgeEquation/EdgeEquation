from core.posting import post_text
from core.formatting import format_edges_morning
from engines.edges import get_morning_edges

def run():
    body = get_morning_edges()
    text = format_edges_morning(body)
    post_text(text)
    return text
