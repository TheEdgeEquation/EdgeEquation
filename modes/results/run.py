from core.posting import post_text
from core.formatting import format_results

def run():
    text = format_results()
    post_text(text)
    return text
