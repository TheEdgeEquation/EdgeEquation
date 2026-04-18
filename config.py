# config.py

import os
from datetime import datetime

# Brand
BRAND_NAME = "Edge Equation"
TAGLINE = "Facts. Not Feelings."

# Paths
OUTPUT_DIR = "out"
OUTPUT_IMAGE_NAME = "edge_equation_daily.png"

def today_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d")

# X / Twitter credentials (read from env so they never hard-code)
X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")

def validate_x_env() -> None:
    missing = [
        name for name, value in [
            ("X_API_KEY", X_API_KEY),
            ("X_API_SECRET", X_API_SECRET),
            ("X_ACCESS_TOKEN", X_ACCESS_TOKEN),
            ("X_ACCESS_TOKEN_SECRET", X_ACCESS_TOKEN_SECRET),
        ] if not value
    ]
    if missing:
        raise RuntimeError(f"Missing X credentials in environment: {', '.join(missing)}")
