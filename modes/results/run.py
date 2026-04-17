from core.posting import post_text
from core.formatting import format_results
from engines.results import get_results

def run():
    body = get_results()
    text = format_results(body)
    post_text(text)
    return text
