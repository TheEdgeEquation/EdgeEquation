from core.posting import post_text
from core.formatting import format_domestic_fact

def run():
    text = format_domestic_fact()
    post_text(text)
    return text
