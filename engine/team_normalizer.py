"""
GLOBAL TEAM NAME NORMALIZER — FULL PRODUCTION VERSION
-----------------------------------------------------

This file ensures that ALL team names from:
  - Odds API
  - Scrapers (KBO, NPB, EPL, UCL)
  - Playoff bracket engine
  - Playoff series engine
  - Posting layer
  - Manual overrides

normalize to ONE canonical name.

Usage:
    from engine.team_normalizer import normalize_team_name
    clean = normalize_team_name(raw_name)
"""

import re

# ---------------------------------------------------------
# CANONICAL TEAM NAMES (THESE ARE THE NAMES YOUR BRAND POSTS)
# ---------------------------------------------------------

# NBA
NBA_TEAMS = {
    "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets",
    "Chicago Bulls", "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets",
    "Detroit Pistons", "Golden State Warriors", "Houston Rockets", "Indiana Pacers",
    "LA Clippers", "Los Angeles Clippers", "Los Angeles Lakers", "Memphis Grizzlies",
    "Miami Heat", "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans",
    "New York Knicks", "Oklahoma City Thunder", "Orlando Magic", "Philadelphia 76ers",
    "Phoenix Suns", "Portland Trail Blazers", "Sacramento Kings", "San Antonio Spurs",
    "Toronto Raptors", "Utah Jazz", "Washington Wizards"
}

# NHL
NHL_TEAMS = {
    "Anaheim Ducks", "Arizona Coyotes", "Boston Bruins", "Buffalo Sabres",
    "Calgary Flames", "Carolina Hurricanes", "Chicago Blackhawks", "Colorado Avalanche",
    "Columbus Blue Jackets", "Dallas Stars", "Detroit Red Wings", "Edmonton Oilers",
    "Florida Panthers", "Los Angeles Kings", "Minnesota Wild", "Montreal Canadiens",
    "Nashville Predators", "New Jersey Devils", "New York Islanders", "New York Rangers",
    "Ottawa Senators", "Philadelphia Flyers", "Pittsburgh Penguins", "San Jose Sharks",
    "Seattle Kraken", "St. Louis Blues", "Tampa Bay Lightning", "Toronto Maple Leafs",
    "Vancouver Canucks", "Vegas Golden Knights", "Washington Capitals", "Winnipeg Jets"
}

# MLB
MLB_TEAMS = {
    "Arizona Diamondbacks", "Atlanta Braves", "Baltimore Orioles", "Boston Red Sox",
    "Chicago Cubs", "Chicago White Sox", "Cincinnati Reds", "Cleveland Guardians",
    "Colorado Rockies", "Detroit Tigers", "Houston Astros", "Kansas City Royals",
    "Los Angeles Angels", "Los Angeles Dodgers", "Miami Marlins", "Milwaukee Brewers",
    "Minnesota Twins", "New York Mets", "New York Yankees", "Oakland Athletics",
    "Philadelphia Phillies", "Pittsburgh Pirates", "San Diego Padres", "San Francisco Giants",
    "Seattle Mariners", "St. Louis Cardinals", "Tampa Bay Rays", "Texas Rangers",
    "Toronto Blue Jays", "Washington Nationals"
}

# NFL
NFL_TEAMS = {
    "Arizona Cardinals", "Atlanta Falcons", "Baltimore Ravens", "Buffalo Bills",
    "Carolina Panthers", "Chicago Bears", "Cincinnati Bengals", "Cleveland Browns",
    "Dallas Cowboys", "Denver Broncos", "Detroit Lions", "Green Bay Packers",
    "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Kansas City Chiefs",
    "Las Vegas Raiders", "Los Angeles Chargers", "Los Angeles Rams", "Miami Dolphins",
    "Minnesota Vikings", "New England Patriots", "New Orleans Saints", "New York Giants",
    "New York Jets", "Philadelphia Eagles", "Pittsburgh Steelers", "San Francisco 49ers",
    "Seattle Seahawks", "Tampa Bay Buccaneers", "Tennessee Titans", "Washington Commanders"
}

# KBO
KBO_TEAMS = {
    "Doosan Bears", "Hanwha Eagles", "KIA Tigers", "Kiwoom Heroes",
    "KT Wiz", "LG Twins", "Lotte Giants", "NC Dinos", "Samsung Lions", "SSG Landers"
}

# NPB
NPB_TEAMS = {
    "Yomiuri Giants", "Hanshin Tigers", "Chunichi Dragons", "Hiroshima Toyo Carp",
    "Yokohama DeNA BayStars", "Tokyo Yakult Swallows",
    "Orix Buffaloes", "Fukuoka SoftBank Hawks", "Hokkaido Nippon-Ham Fighters",
    "Saitama Seibu Lions", "Tohoku Rakuten Golden Eagles", "Chiba Lotte Marines"
}

# EPL
EPL_TEAMS = {
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
    "Burnley", "Chelsea", "Crystal Palace", "Everton", "Fulham",
    "Liverpool", "Luton Town", "Manchester City", "Manchester United",
    "Newcastle United", "Nottingham Forest", "Sheffield United",
    "Tottenham Hotspur", "West Ham United", "Wolves"
}

# UCL (clubs vary year to year, but these are the canonical forms)
UCL_TEAMS = {
    "Real Madrid", "Barcelona", "Atletico Madrid", "Sevilla",
    "Bayern Munich", "Borussia Dortmund", "RB Leipzig", "Bayer Leverkusen",
    "Paris Saint-Germain", "Marseille", "Lille",
    "Inter Milan", "AC Milan", "Juventus", "Napoli", "Roma", "Lazio",
    "Manchester City", "Manchester United", "Arsenal", "Chelsea", "Liverpool",
    "Benfica", "Porto", "Sporting CP",
    "Ajax", "PSV Eindhoven", "Feyenoord",
    "Celtic", "Rangers",
    "Shakhtar Donetsk", "Dynamo Kyiv",
    "Galatasaray", "Fenerbahce",
    "Red Bull Salzburg", "Copenhagen",
}

# ---------------------------------------------------------
# BUILD ALIAS MAP
# ---------------------------------------------------------

TEAM_ALIASES = {}

def _add_alias(alias, canonical):
    TEAM_ALIASES[alias.lower()] = canonical

def _generate_aliases(team_set):
    for team in team_set:
        lower = team.lower()
        _add_alias(lower, team)

        # Remove FC, CF, SC, BC, etc.
        cleaned = re.sub(r"\b(fc|cf|sc|bc)\b\.?", "", lower).strip()
        if cleaned != lower:
            _add_alias(cleaned, team)

        # Remove city prefixes (e.g., "Manchester City" → "City")
        parts = lower.split()
        if len(parts) > 1:
            _add_alias(parts[-1], team)

        # Abbreviations (e.g., "Los Angeles" → "LA")
        if "los angeles" in lower:
            _add_alias(lower.replace("los angeles", "la"), team)
            _add_alias(lower.replace("los angeles", "l.a."), team)

        # Common short forms
        if "united" in lower:
            _add_alias("man united", "Manchester United")
            _add_alias("man utd", "Manchester United")
            _add_alias("man u", "Manchester United")

        if "hotspur" in lower:
            _add_alias("spurs", "Tottenham Hotspur")

        if "saint-germain" in lower:
            _add_alias("psg", "Paris Saint-Germain")

        if "baystars" in lower:
            _add_alias("dena", "Yokohama DeNA BayStars")
            _add_alias("baystars", "Yokohama DeNA BayStars")

        if "twins" in lower:
            _add_alias("lg", "LG Twins")

        if "tigers" in lower:
            _add_alias("kia", "KIA Tigers")
            _add_alias("hanshin", "Hanshin Tigers")

# Generate aliases for all leagues
for league in [
    NBA_TEAMS, NHL_TEAMS, MLB_TEAMS, NFL_TEAMS,
    KBO_TEAMS, NPB_TEAMS, EPL_TEAMS, UCL_TEAMS
]:
    _generate_aliases(league)

# ---------------------------------------------------------
# NORMALIZER
# ---------------------------------------------------------

def normalize_team_name(name: str) -> str:
    if not name:
        return name

    raw = name.strip().lower()

    # Direct match
    if raw in TEAM_ALIASES:
        return TEAM_ALIASES[raw]

    # Fuzzy contains match
    for alias, canonical in TEAM_ALIASES.items():
        if alias in raw:
            return canonical

    # Title-case fallback
    return " ".join(w.capitalize() for w in raw.split())
