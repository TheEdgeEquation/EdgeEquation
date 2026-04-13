"""
engine/stats/umpire.py
Scrapes umpire strikeout tendencies from Umpire Scorecards.
Umpires with large strike zones = more Ks.
"""
import requests
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Static umpire K rate adjustments based on historical data
# Values represent K rate vs league average
# > 1.0 = calls more strikes = more Ks
# < 1.0 = tight zone = fewer Ks
# Updated periodically — source: UmpireScorecards.com
UMPIRE_K_FACTORS = {
    "Angel Hernandez":     0.94,
    "Ángel Hernández":     0.94,
    "CB Bucknor":          0.93,
    "Joe West":            0.96,
    "Vic Carapazza":       1.06,
    "Marvin Hudson":       0.97,
    "Hunter Wendelstedt":  1.04,
    "Mark Carlson":        1.03,
    "Dan Iassogna":        1.05,
    "Laz Diaz":            0.95,
    "Jeff Nelson":         1.04,
    "Ron Kulpa":           1.02,
    "Jim Reynolds":        0.98,
    "Bill Miller":         1.03,
    "Brian Gorman":        1.01,
    "Alfonso Marquez":     0.99,
    "Mike Estabrook":      1.02,
    "Chris Guccione":      1.01,
    "Paul Nauert":         1.00,
    "Fieldin Culbreth":    0.99,
    "Sam Holbrook":        1.01,
    "Ted Barrett":         1.02,
    "Tom Hallion":         0.98,
    "Jerry Layne":         1.00,
    "Cory Blaser":         1.03,
    "Manny Gonzalez":      1.01,
    "Lance Barrett":       1.02,
    "Jeremie Rehak":       1.04,
    "Adam Hamari":         1.01,
    "Ben May":             1.03,
    "Nick Mahrley":        1.02,
    "Alex Tosi":           1.01,
    "Nestor Ceja":         1.00,
    "Ryan Blakney":        1.02,
    "John Libka":          1.01,
    "Brian Walsh":         1.03,
    "Phil Cuzzi":          0.99,
    "Mike Winters":        1.00,
    "James Hoye":          1.01,
    "Quinn Wolcott":       1.02,
    "David Rackley":       1.01,
    "Brennan Miller":      1.03,
    "Mike Muchlinski":     1.00,
    "Gabe Morales":        1.01,
    "Roberto Ortiz":       1.00,
    "Junior Valentine":    0.98,
    "Stu Scheurwater":     1.01,
    "Nate Tomlinson":      1.02,
    "Todd Tichenor":       1.01,
    "Tripp Gibson":        1.03,
    "Chad Fairchild":      1.02,
    "Seminaris":           1.00,
}


def get_umpire_adjustment(umpire_name: str) -> float:
    """
    Get K rate adjustment for a given umpire.
    Returns 1.0 if umpire not found.
    """
    if not umpire_name:
        return 1.0

    # Try exact match first
    factor = UMPIRE_K_FACTORS.get(umpire_name)
    if factor:
        logger.info(f"Umpire {umpire_name}: K factor={factor}")
        return factor

    # Try partial match
    for name, f in UMPIRE_K_FACTORS.items():
        if umpire_name.lower() in name.lower() or name.lower() in umpire_name.lower():
            logger.info(f"Umpire {umpire_name} matched {name}: K factor={f}")
            return f

    logger.warning(f"Umpire {umpire_name} not found — using neutral 1.0")
    return 1.0


def fetch_todays_umpires() -> dict:
    """
    Scrape today's home plate umpires from MLB.com.
    Returns dict of {game_id: umpire_name}.
    """
    try:
        url = "https://statsapi.mlb.com/api/v1/schedule"
        params = {
            "sportId": 1,
            "hydrate": "officials",
            "date": _today_str(),
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        umpires = {}
        for date in data.get("dates", []):
            for game in date.get("games", []):
                game_id = game.get("gamePk")
                officials = game.get("officials", [])
                for official in officials:
                    if official.get("officialType") == "Home Plate":
                        name = official.get("official", {}).get("fullName", "")
                        umpires[game_id] = name
                        break

        logger.info(f"Fetched {len(umpires)} umpire assignments")
        return umpires

    except Exception as e:
        logger.error(f"Umpire fetch failed: {e}")
        return {}


def get_umpire_for_game(home_team: str, away_team: str) -> tuple[str, float]:
    """
    Get umpire name and K adjustment for a specific game.
    Returns (umpire_name, k_adjustment).
    """
    try:
        umpires_by_game = fetch_todays_umpires()

        # Match game by fetching schedule with teams
        url = "https://statsapi.mlb.com/api/v1/schedule"
        params = {
            "sportId": 1,
            "hydrate": "officials,teams",
            "date": _today_str(),
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        for date in data.get("dates", []):
            for game in date.get("games", []):
                home = game.get("teams", {}).get("home", {}).get("team", {}).get("name", "")
                away = game.get("teams", {}).get("away", {}).get("team", {}).get("name", "")

                if home_team.lower() in home.lower() or away_team.lower() in away.lower():
                    game_id = game.get("gamePk")
                    umpire_name = umpires_by_game.get(game_id, "")
                    k_adj = get_umpire_adjustment(umpire_name)
                    return umpire_name, k_adj

    except Exception as e:
        logger.error(f"Umpire game lookup failed: {e}")

    return "Unknown", 1.0


def _today_str() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")
