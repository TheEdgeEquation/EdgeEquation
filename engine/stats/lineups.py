import requests
from datetime import datetime

def get_today_batters(league):
    if league == "MLB":
        return get_today_batters_mlb()
    if league == "KBO":
        return get_today_batters_kbo()
    if league == "NPB":
        return get_today_batters_npb()
    return []


    url = "https://statsapi.mlb.com/api/v1/schedule"
    params = {"sportId": 1, "hydrate": "probablePitcher,team,lineups", "date": datetime.now().strftime("%Y-%m-%d")}
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()

    batters = []
    for date in data.get("dates", []):
        for game in date.get("games", []):
            home = game.get("teams", {}).get("home", {})
            away = game.get("teams", {}).get("away", {})
            home_team = home.get("team", {}).get("name", "")
            away_team = away.get("team", {}).get("name", "")
            commence = game.get("gameDate", "")

            for side, team_name, opp_name in [
                ("home", home_team, away_team),
                ("away", away_team, home_team),
            ]:
                lineup = game.get("lineups", {}).get(side, {}).get("battingOrder", [])
                for entry in lineup:
                    player = entry.get("fullName")
                    if player:
                        batters.append({
                            "player": player,
                            "team": team_name,
                            "opponent": opp_name,
                            "commence_time": commence,
                        })

    return batters

def get_today_batters_kbo():
    # Simple stub — replace with real scraper later
    return []

def get_today_batters_npb():
    # Simple stub — replace with real scraper later
    return []

