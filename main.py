# main.py

import argparse
import sys
from modes import MODES

def main():
    parser = argparse.ArgumentParser(description="Edge Equation Mode Runner")
    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        help="Mode to run (see MODES in modes/__init__.py)"
    )
    args = parser.parse_args()
    mode = args.mode.strip()

    if mode not in MODES:
        print(f"[ERROR] Unknown mode: {mode}")
        print(f"Available modes: {', '.join(MODES.keys())}")
        sys.exit(1)

    print(f"[INFO] Running mode: {mode}")
    try:
        MODES[mode]()   # Execute the selected mode
    except Exception as e:
        print(f"[ERROR] Mode '{mode}' failed: {e}")
        sys.exit(1)

    print(f"[INFO] Mode '{mode}' completed successfully.")

if __name__ == "__main__":
    main()
