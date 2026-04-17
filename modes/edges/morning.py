from core.posting import post_text
from core.formatting import format_edges_morning
from engines.edges import get_morning_edges  # this is the standard engine call

def run():
    # 1. Get the raw engine output (the "body")
    body = get_morning_edges()

    # 2. Format it using the formatter that expects `body`
    text = format_edges_morning(body)

    # 3. Post it
    post_text(text)

    return text
