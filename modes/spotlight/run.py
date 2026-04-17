from core.posting import post_to_x
from core.formatting import format_spotlight

def run():
    text = format_spotlight()
    post_to_x(text)
    return text
