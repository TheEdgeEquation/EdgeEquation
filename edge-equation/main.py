# main.py
import argparse

from engines.facts import post_domestic_fact, post_overseas_fact
# we'll add more imports later as we build other engines


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, help="Which posting mode to run")
    args = parser.parse_args()

    if args.mode == "fact_domestic":
        post_domestic_fact()
    elif args.mode == "fact_overseas":
        post_overseas_fact()
    else:
        raise SystemExit(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    main()
