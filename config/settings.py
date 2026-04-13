"""
EdgeEquation + Cash Before Coffee — Central Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────────
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "7d57ca787d268998f2d9bcc6a5eaa55c")
X_API_KEY = os.getenv("X_API_KEY", "")
X_API_SECRET = os.getenv("X_API_SECRET", "")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN", "")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# ── Odds API ──────────────────────────────────────────────────────────────────
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
ODDS_API_REGIONS = "us"
ODDS_API_FORMAT = "american"

# ── Sports & Markets (player props only) ─────────────────────────────────────
SPORT_MARKETS = {
    "baseball_mlb": {
        "market": "batter_strikeouts",
        "label": "MLB",
        "prop_label": "Strikeouts",
        "icon": "⚾",
    },
    "basketball_nba": {
        "market": "player_threes",
        "label": "NBA",
        "prop_label": "3-Pointers",
        "icon": "🏀",
    },
    "icehockey_nhl": {
        "market": "player_shots_on_goal",
        "label": "NHL",
        "prop_label": "Shots on Goal",
        "icon": "🏒",
    },
    "americanfootball_nfl": {
        "market": "player_receptions",
        "label": "NFL",
        "prop_label": "Receptions",
        "icon": "🏈",
    },
}

# ── NRFI/YRFI — typical book implied probabilities ───────────────────────────
# Books typically price NRFI at -130 to -150 (implied 57-60%)
# We calculate our own probability and compare
NRFI_TYPICAL_JUICE = -135       # typical book price for NRFI
YRFI_TYPICAL_JUICE = +115       # typical book price for YRFI

def american_to_implied(odds: int) -> float:
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)

NRFI_IMPLIED = american_to_implied(NRFI_TYPICAL_JUICE)
YRFI_IMPLIED = american_to_implied(YRFI_TYPICAL_JUICE)

# ── Monte Carlo ───────────────────────────────────────────────────────────────
MC_SIMULATIONS = 10_000

# ── Grade thresholds ──────────────────────────────────────────────────────────
GRADE_THRESHOLDS = [
    ("A+", 0.08, 91, "Sigma Play"),
    ("A",  0.06, 90, "Precision Play"),
    ("A-", 0.04, 88, "Sharp Play"),
]

# ── ESPN CDN logo URL template ────────────────────────────────────────────────
ESPN_LOGO_MLB = "https://a.espncdn.com/i/teamlogos/mlb/500/{abbr}.png"
ESPN_LOGO_NBA = "https://a.espncdn.com/i/teamlogos/nba/500/{abbr}.png"
ESPN_LOGO_NHL = "https://a.espncdn.com/i/teamlogos/nhl/500/{abbr}.png"
ESPN_LOGO_NFL = "https://a.espncdn.com/i/teamlogos/nfl/500/{abbr}.png"

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")

# ── Graphic dimensions ────────────────────────────────────────────────────────
GRAPHIC_WIDTH  = 1200
GRAPHIC_HEIGHT = 800

# ── Branding ──────────────────────────────────────────────────────────────────
EE_TAGLINE   = "Live data. 100% Verified. No feelings. Just facts."
CBC_TAGLINE  = "Cash While You Sleep."
ALGO_VERSION = "ALGORITHM v2.0"
