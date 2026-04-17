from core.posting import post_text
from core.formatting import format_spotlight

def run():
    text = format_spotlight()
    post_text(text)
    return text
