from core.posting import post_to_x
from core.formatting import format_domestic_fact

def run():
    text = format_domestic_fact()
    post_to_x(text)
    return text
