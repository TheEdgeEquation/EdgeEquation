# stats"""
engine/stats/park_factors.py
Static park factors for MLB stadiums.
K factor > 1.0 means park inflates strikeouts.
K factor < 1.0 means park suppresses strikeouts.
Dome = True means weather is irrelevant.
Altitude in feet — affects pitch movement.
"""

PARK_FACTORS = {
    # Team: {k_factor, dome, altitude, name}
    "Arizona Diamondbacks":    {"k_factor": 0.97, "dome": True,  "altitude": 1082, "name": "Chase Field"},
    "Atlanta Braves":          {"k_factor": 1.02, "dome": False, "altitude": 1050, "name": "Truist Park"},
    "Baltimore Orioles":       {"k_factor": 0.98, "dome": False, "altitude": 20,   "name": "Oriole Park"},
    "Boston Red Sox":          {"k_factor": 0.96, "dome": False, "altitude": 20,   "name": "Fenway Park"},
    "Chicago Cubs":            {"k_factor": 1.01, "dome": False, "altitude": 595,  "name": "Wrigley Field"},
    "Chicago White Sox":       {"k_factor": 0.99, "dome": False, "altitude": 595,  "name": "Guaranteed Rate Field"},
    "Cincinnati Reds":         {"k_factor": 1.00, "dome": False, "altitude": 550,  "name": "Great American Ball Park"},
    "Cleveland Guardians":     {"k_factor": 1.01, "dome": False, "altitude": 653,  "name": "Progressive Field"},
    "Colorado Rockies":        {"k_factor": 0.88, "dome": False, "altitude": 5200, "name": "Coors Field"},
    "Detroit Tigers":          {"k_factor": 1.00, "dome": False, "altitude": 585,  "name": "Comerica Park"},
    "Houston Astros":          {"k_factor": 1.03, "dome": True,  "altitude": 43,   "name": "Minute Maid Park"},
    "Kansas City Royals":      {"k_factor": 0.98, "dome": False, "altitude": 909,  "name": "Kauffman Stadium"},
    "Los Angeles Angels":      {"k_factor": 0.99, "dome": False, "altitude": 160,  "name": "Angel Stadium"},
    "Los Angeles Dodgers":     {"k_factor": 1.02, "dome": False, "altitude": 515,  "name": "Dodger Stadium"},
    "Miami Marlins":           {"k_factor": 1.04, "dome": True,  "altitude": 6,    "name": "loanDepot Park"},
    "Milwaukee Brewers":       {"k_factor": 1.01, "dome": True,  "altitude": 635,  "name": "American Family Field"},
    "Minnesota Twins":         {"k_factor": 1.00, "dome": False, "altitude": 815,  "name": "Target Field"},
    "New York Mets":           {"k_factor": 1.01, "dome": False, "altitude": 20,   "name": "Citi Field"},
    "New York Yankees":        {"k_factor": 1.00, "dome": False, "altitude": 20,   "name": "Yankee Stadium"},
    "Oakland Athletics":       {"k_factor": 0.97, "dome": False, "altitude": 25,   "name": "Oakland Coliseum"},
    "Philadelphia Phillies":   {"k_factor": 1.01, "dome": False, "altitude": 20,   "name": "Citizens Bank Park"},
    "Pittsburgh Pirates":      {"k_factor": 0.99, "dome": False, "altitude": 730,  "name": "PNC Park"},
    "San Diego Padres":        {"k_factor": 1.00, "dome": False, "altitude": 17,   "name": "Petco Park"},
    "San Francisco Giants":    {"k_factor": 1.03, "dome": False, "altitude": 52,   "name": "Oracle Park"},
    "Seattle Mariners":        {"k_factor": 1.02, "dome": True,  "altitude": 17,   "name": "T-Mobile Park"},
    "St. Louis Cardinals":     {"k_factor": 0.99, "dome": False, "altitude": 466,  "name": "Busch Stadium"},
    "Tampa Bay Rays":          {"k_factor": 1.03, "dome": True,  "altitude": 15,   "name": "Tropicana Field"},
    "Texas Rangers":           {"k_factor": 1.01, "dome": True,  "altitude": 551,  "name": "Globe Life Field"},
    "Toronto Blue Jays":       {"k_factor": 1.00, "dome": True,  "altitude": 250,  "name": "Rogers Centre"},
    "Washington Nationals":    {"k_factor": 1.00, "dome": False, "altitude": 25,   "name": "Nationals Park"},
}


def get_park_factor(home_team: str) -> dict:
    """Get park factor data for a home team."""
    return PARK_FACTORS.get(home_team, {
        "k_factor": 1.0,
        "dome": False,
        "altitude": 100,
        "name": "Unknown Park"
    })


def get_k_factor(home_team: str) -> float:
    """Get strikeout park factor for a home team."""
    return get_park_factor(home_team)["k_factor"]


def is_dome(home_team: str) -> bool:
    """Returns True if the home team plays in a dome."""
    return get_park_factor(home_team)["dome"]


def get_altitude_adjustment(home_team: str) -> float:
    """
    Altitude affects pitch movement — higher altitude = less break = fewer Ks.
    Coors Field is the extreme case (5200 ft).
    Returns adjustment multiplier.
    """
    alt = get_park_factor(home_team).get("altitude", 100)
    if alt > 4000:
        return 0.92   # Coors extreme
    elif alt > 2000:
        return 0.96
    elif alt > 1000:
        return 0.98
    return 1.0 package
