from core.posting import post_text
from core.formatting import format_spotlight
from engines.spotlight import get_spotlight

def run():
    body = get_spotlight()
    text = format_spotlight(body)
    post_text(text)
    return text
