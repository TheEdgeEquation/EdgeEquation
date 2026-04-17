# main.py
import argparse

from engines.facts import post_domestic_fact, post_overseas_fact
from engines.spotlight import post_spotlight_insight
from engines.edges import post_morning_edges, post_evening_edges
from engines.results import post_results_if_any


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, help="Which posting mode to run")
    args = parser.parse_args()

    if args.mode == "fact_domestic":
        post_domestic_fact()

    elif args.mode == "fact_overseas":
        post_overseas_fact()

    elif args.mode == "spotlight":
        post_spotlight_insight()

    elif args.mode == "edges_morning":
        post_morning_edges()

    elif args.mode == "edges_evening":
        post_evening_edges()

    elif args.mode == "results":
        post_results_if_any()

    else:
        raise SystemExit(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    main()
