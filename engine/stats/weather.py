"""
engine/stats/weather.py
Fetches weather for MLB stadiums using OpenWeatherMap API.
Weather affects strikeouts — cold temp, wind in = more Ks.
Domes bypass weather entirely.
"""
import os
import requests
import logging
from engine.stats.park_factors import is_dome

logger = logging.getLogger(__name__)

OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY", "")

STADIUM_COORDS = {
    "Arizona Diamondbacks":    (33.4453, -112.0667),
    "Atlanta Braves":          (33.8908, -84.4677),
    "Baltimore Orioles":       (39.2838, -76.6216),
    "Boston Red Sox":          (42.3467, -71.0972),
    "Chicago Cubs":            (41.9484, -87.6553),
    "Chicago White Sox":       (41.8299, -87.6338),
    "Cincinnati Reds":         (39.0979, -84.5082),
    "Cleveland Guardians":     (41.4962, -81.6852),
    "Colorado Rockies":        (39.7559, -104.9942),
    "Detroit Tigers":          (42.3390, -83.0485),
    "Houston Astros":          (29.7572, -95.3555),
    "Kansas City Royals":      (39.0517, -94.4803),
    "Los Angeles Angels":      (33.8003, -117.8827),
    "Los Angeles Dodgers":     (34.0739, -118.2400),
    "Miami Marlins":           (25.7781, -80.2197),
    "Milwaukee Brewers":       (43.0280, -87.9712),
    "Minnesota Twins":         (44.9817, -93.2778),
    "New York Mets":           (40.7571, -73.8458),
    "New York Yankees":        (40.8296, -73.9262),
    "Oakland Athletics":       (37.7516, -122.2005),
    "Philadelphia Phillies":   (39.9061, -75.1665),
    "Pittsburgh Pirates":      (40.4469, -80.0057),
    "San Diego Padres":        (32.7073, -117.1573),
    "San Francisco Giants":    (37.7786, -122.3893),
    "Seattle Mariners":        (47.5914, -122.3323),
    "St. Louis Cardinals":     (38.6226, -90.1928),
    "Tampa Bay Rays":          (27.7683, -82.6534),
    "Texas Rangers":           (32.7513, -97.0832),
    "Toronto Blue Jays":       (43.6414, -79.3894),
    "Washington Nationals":    (38.8730, -77.0074),
}


def get_weather(home_team: str) -> dict:
    """
    Fetch current weather for a stadium.
    Returns dict with temp_f, wind_mph, wind_dir, condition, dome.
    """
    if is_dome(home_team):
        logger.info(f"{home_team} plays in a dome — weather irrelevant")
        return {
            "temp_f": 72,
            "wind_mph": 0,
            "wind_dir": "N/A",
            "condition": "Dome",
            "dome": True,
            "k_adjustment": 1.0,
        }

    coords = STADIUM_COORDS.get(home_team)
    if not coords:
        logger.warning(f"No coords for {home_team}")
        return _neutral_weather()

    if not OPENWEATHER_KEY:
        logger.warning("OPENWEATHER_API_KEY not set")
        return _neutral_weather()

    lat, lon = coords
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_KEY,
        "units": "imperial",
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        temp_f    = data["main"]["temp"]
        wind_mph  = data["wind"]["speed"]
        wind_deg  = data["wind"].get("deg", 0)
        condition = data["weather"][0]["main"]

        wind_dir = _degrees_to_direction(wind_deg)
        k_adj    = _calculate_k_adjustment(temp_f, wind_mph, wind_dir, condition)

        logger.info(f"{home_team}: {temp_f}F, {wind_mph}mph {wind_dir}, {condition} → K adj={k_adj}")

        return {
            "temp_f": round(temp_f, 1),
            "wind_mph": round(wind_mph, 1),
            "wind_dir": wind_dir,
            "condition": condition,
            "dome": False,
            "k_adjustment": k_adj,
        }

    except Exception as e:
        logger.error(f"Weather fetch failed for {home_team}: {e}")
        return _neutral_weather()


def _neutral_weather() -> dict:
    return {
        "temp_f": 70,
        "wind_mph": 5,
        "wind_dir": "N",
        "condition": "Clear",
        "dome": False,
        "k_adjustment": 1.0,
    }


def _degrees_to_direction(deg: float) -> str:
    dirs = ["N","NE","E","SE","S","SW","W","NW"]
    idx = round(deg / 45) % 8
    return dirs[idx]


def _calculate_k_adjustment(temp_f, wind_mph, wind_dir, condition) -> float:
    """
    Calculate strikeout adjustment based on weather conditions.
    Cold + wind in = more Ks. Hot + wind out = fewer Ks.
    """
    adj = 1.0

    # Temperature effect
    if temp_f < 40:
        adj *= 1.06   # very cold = batters struggle
    elif temp_f < 50:
        adj *= 1.04
    elif temp_f < 60:
        adj *= 1.02
    elif temp_f > 85:
        adj *= 0.98   # hot = looser muscles = better contact
    elif temp_f > 95:
        adj *= 0.96

    # Wind effect — wind blowing IN suppresses offense = more Ks
    # Wind blowing OUT inflates offense = fewer Ks
    if wind_mph > 15:
        if wind_dir in ("N", "NE", "NW"):
            adj *= 1.03   # wind in at most parks
        elif wind_dir in ("S", "SE", "SW"):
            adj *= 0.97   # wind out at most parks
    elif wind_mph > 25:
        if wind_dir in ("N", "NE", "NW"):
            adj *= 1.05
        elif wind_dir in ("S", "SE", "SW"):
            adj *= 0.94

    # Rain/overcast — slight suppression on offense
    if condition in ("Rain", "Drizzle", "Thunderstorm"):
        adj *= 1.02
    elif condition == "Snow":
        adj *= 1.04

    return round(adj, 4)
