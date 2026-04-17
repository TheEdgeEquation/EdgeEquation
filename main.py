import sys
import logging
from modes import MODES

# ------------------------------------------------------------
# Logging Configuration
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# Main Dispatcher
# ------------------------------------------------------------
def main():
    """
    Entry point for Edge Equation 3.0.
    Usage:
        python main.py <mode>

    Example:
        python main.py daily_email
        python main.py gotd
        python main.py primary_signal
    """
    if len(sys.argv) < 2:
        print("\nUsage: python main.py <mode>\n")
        print("Available modes:")
        for m in sorted(MODES.keys()):
            print(f"  - {m}")
        print()
        return

    mode = sys.argv[1]

    if mode not in MODES:
        print(f"\nUnknown mode: {mode}\n")
        print("Available modes:")
        for m in sorted(MODES.keys()):
            print(f"  - {m}")
        print()
        return

    logger.info(f"MODE: {mode}")
    try:
        MODES[mode]()   # No dry_run / no_graphic
    except Exception as e:
        logger.error(f"Mode '{mode}' failed: {e}")


# ------------------------------------------------------------
# Entrypoint Guard
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
