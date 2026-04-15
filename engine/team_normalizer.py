"""
Team Name Normalizer
--------------------

This module ensures that ALL team names used across:
  - Odds API
  - Playoff engine
  - Bracket engine
  - Overseas scrapers
  - Posting layer

are normalized to a single canonical name.

Usage:
    from engine.team_normalizer import normalize_team_name
    clean = normalize_team_name(raw_name)
"""

import re

# ---------------------------------------------------------
# GLOBAL ALIAS MAP
# ---------------------------------------------------------
# Keys = lowercase patterns you expect to see
# Values = canonical team names used in your model + posting layer
# ---------------------------------------------------------

TEAM_ALIASES = {
    # -------------------------
    # NBA
    # -------------------------
    "la clippers": "Los Angeles Clippers",
    "l.a. clippers": "Los Angeles Clippers",
    "los angeles clippers": "Los Angeles Clippers",

    "la lakers": "Los Angeles Lakers",
    "l.a. lakers": "Los Angeles Lakers",
    "los angeles lakers": "Los Angeles Lakers",

    "gs warriors": "Golden State Warriors",
    "g.s. warriors": "Golden State Warriors",
    "golden state": "Golden State Warriors",

    # -------------------------
    # NHL
    # -------------------------
    "tampa bay lightning": "Tampa Bay Lightning",
    "tbl": "Tampa Bay Lightning",

    "toronto maple leafs": "Toronto Maple Leafs",
    "leafs": "Toronto Maple Leafs",

    # -------------------------
    # MLB
    # -------------------------
    "la dodgers": "Los Angeles Dodgers",
    "dodgers": "Los Angeles Dodgers",

    "ny yankees": "New York Yankees",
    "yankees": "New York Yankees",

    # -------------------------
    # NFL
    # -------------------------
    "kc chiefs": "Kansas City Chiefs",
    "chiefs": "Kansas City Chiefs",

    "sf 49ers": "San Francisco 49ers",
    "49ers": "San Francisco 49ers",

    # -------------------------
    # KBO
    # -------------------------
    "lg twins": "LG Twins",
    "twins": "LG Twins",

    "doosan bears": "Doosan Bears",
    "bears": "Doosan Bears",

    "kia tigers": "KIA Tigers",
    "tigers": "KIA Tigers",

    # -------------------------
    # NPB
    # -------------------------
    "yokohama dena baystars": "Yokohama DeNA BayStars",
    "dena baystars": "Yokohama DeNA BayStars",
    "baystars": "Yokohama DeNA BayStars",

    "hanshin tigers": "Hanshin Tigers",

    # -------------------------
    # EPL
    # -------------------------
    "manchester united": "Manchester United",
    "man united": "Manchester United",
    "man utd": "Manchester United",
    "man u": "Manchester United",

    "manchester city": "Manchester City",
    "man city": "Manchester City",
    "man c": "Manchester City",

    "tottenham hotspur": "Tottenham Hotspur",
    "spurs": "Tottenham Hotspur",

    # -------------------------
    # UCL / UEFA
    # -------------------------
    "paris saint-germain": "Paris Saint-Germain",
    "psg": "Paris Saint-Germain",

    "real madrid": "Real Madrid",
    "madrid": "Real Madrid",
}


# ---------------------------------------------------------
# NORMALIZER FUNCTION
# ---------------------------------------------------------

def normalize_team_name(name: str) -> str:
    """
    Normalize ANY raw team name into your canonical internal name.
    """
    if not name:
        return name

    raw = name.strip().lower()

    # Direct alias match
    if raw in TEAM_ALIASES:
        return TEAM_ALIASES[raw]

    # Fuzzy match (contains)
    for alias, canonical in TEAM_ALIASES.items():
        if alias in raw:
            return canonical

    # Title-case fallback
    return " ".join(w.capitalize() for w in raw.split())
