from fetch_props import fetch_props
from engagement_check import engagement_check
from file_io import save_output
from post_to_x import post_to_x
from logger import log

def main():
    log("Starting Edge Equation Engine (Launch Mode: ALWAYS POST)")

    # 1. Fetch props
    log("Fetching props...")
    props = fetch_props()
    log(f"Fetched {len(props)} props")

    # 2. Build card (placeholder for now)
    log("Building card...")
    card = {
        "date": "",
        "tiers": "",
        "metadata": "",
        "props": props
    }
    log("Card built")

    # 3. Save output
    log("Saving output...")
    save_output(card)
    log("Output saved")

    # 4. Post to X (always, during launch)
    log("Posting to X...")
    post_to_x(card)
    log("Posted to X")

    log("Engine completed successfully")

if __name__ == "__main__":
    main()

