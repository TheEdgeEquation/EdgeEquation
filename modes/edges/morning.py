from core.posting import post_text
from core.formatting import format_edges_morning

def run():
    text = format_edges_morning()
    post_text(text)
    return text

