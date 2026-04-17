from core.posting import post_text
from core.formatting import format_edges_evening

def run():
    text = format_edges_evening()
    post_text(text)
    return text
