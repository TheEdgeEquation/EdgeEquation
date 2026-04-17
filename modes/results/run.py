from core.posting import post_to_x
from core.formatting import format_results

def run():
    text = format_results()
    post_to_x(text)
    return text
