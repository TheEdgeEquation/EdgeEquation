from core.posting import post_to_x
from core.formatting import format_edges_evening

def run():
    text = format_edges_evening()
    post_to_x(text)
    return text
