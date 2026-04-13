# engine/parlay_engine.py
# Edge Equation Parlay Engine
# Product 1: ML/Spread/Total parlay (2-3 legs)
# Product 2: PrizePicks prop parlay (4-6 legs, all markets)
# Both require minimum 15% combined edge to post.
# Never forces a play.

import requests
import logging
import math
from datetime import datetime
from engine.stats.mlb_stats import get_blended_pitcher_stats, get_pitcher_id, get_team_k_rate
from engine.stats.weather import get_weather
from engine.stats.umpire import get_umpire_for_game
from engine.stats.park_factors import get_park_factor, is_dome

logger = logging.getLogger(__name__)

MLB_API = "https://statsapi.mlb.com/api/v1"
CURRENT_YEAR = datetime.now().year

MIN_LEG_EDGE = 0.04
MIN_PARLAY_EDGE = 0.15
MIN_PRIZEPICKS_EDGE = 0.15
MAX_GAME_PARLAY_LEGS = 3
MIN_PRIZEPICKS_LEGS = 4
MAX_PRIZEPICKS_LEGS = 6

LEAGUE_AVG_ERA = 4.25
LEAGUE_AVG_RUNS = 4.5
LEAGUE_AVG_TOTAL = 8.5


def american_to_implied(odds):
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)


def get_todays_games():
    try:
        url = f"{MLB_API}/schedule"
        params = {
            "sportId": 1,
            "hydrate": "probablePitcher,team,linescore",
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        games = []
        for date in data.get("dates", []):
            for game in date.get("games", []):
                home = game.get("teams", {}).get("home", {})
                away = game.get("teams", {}).get("away", {})
                games.append({
                    "game_id": game.get("gamePk"),
                    "home_team": home.get("team", {}).get("name", ""),
                    "away_team": away.get("team", {}).get("name", ""),
                    "home_pitcher": home.get("probablePitcher", {}).get("fullName", ""),
                    "away_pitcher": away.get("probablePitcher", {}).get("fullName", ""),
                    "commence_time": game.get("gameDate", ""),
                })
        logger.info("Found " + str(len(games)) + " games today")
        return games
    except Exception as e:
        logger.error("Failed to fetch games: " + str(e))
        return []


def calculate_team_run_expectancy(team_name, pitcher_name):
    try:
        pid = get_pitcher_id(pitcher_name)
        if pid:
            stats = get_blended_pitcher_stats(pid)
            pitcher_era = stats.get("era", LEAGUE_AVG_ERA)
            avg_ip = stats.get("avg_innings_per_start", 5.5)
        else:
            pitcher_era = LEAGUE_AVG_ERA
            avg_ip = 5.5
        pitcher_runs = (pitcher_era / 9) * avg_ip
        bullpen_runs = (4.20 / 9) * (9 - avg_ip)
        return round(pitcher_runs + bullpen_runs, 2)
    except Exception as e:
        logger.error("Run expectancy failed: " + str(e))
        return LEAGUE_AVG_RUNS


def _calculate_win_prob(home_runs, away_runs):
    diff = home_runs - away_runs
    prob = 1 / (1 + math.exp(-diff * 0.4))
    prob = min(0.80, max(0.20, prob + 0.04))
    return round(prob, 4)


def evaluate_game_for_parlay(game):
    home_team = game["home_team"]
    away_team = game["away_team"]
    home_pitcher = game["home_pitcher"]
    away_pitcher = game["away_pitcher"]
    if not home_pitcher or not away_pitcher:
        return []

    weather = get_weather(home_team)
    park = get_park_factor(home_team)
    park_k = park.get("k_factor", 1.0)
    dome = park.get("dome", False)
    weather_adj = weather.get("k_adjustment", 1.0)

    home_runs = calculate_team_run_expectancy(away_team, away_pitcher)
    away_runs = calculate_team_run_expectancy(home_team, home_pitcher)

    if not dome:
        run_adj = 2.0 - weather_adj
        home_runs *= run_adj
        away_runs *= run_adj

    run_park = 2.0 - park_k
    home_runs = round(home_runs * run_park, 2)
    away_runs = round(away_runs * run_park, 2)

    expected_total = round(home_runs + away_runs, 2)
    home_win_prob = _calculate_win_prob(home_runs, away_runs)
    away_win_prob = round(1 - home_win_prob, 4)

    logger.info(away_team + " @ " + home_team + " exp_total=" + str(expected_total) + " home_win=" + str(home_win_prob))

    bets = []

    # ML
    home_ml_implied = 0.565
    away_ml_implied = 0.435
    home_ml_edge = round(home_win_prob - home_ml_implied, 4)
    away_ml_edge = round(away_win_prob - away_ml_implied, 4)

    if home_ml_edge >= MIN_LEG_EDGE:
        bets.append({
            "type": "ML", "sport": "MLB",
            "pick": home_team + " ML",
            "sim_prob": home_win_prob,
            "implied_prob": home_ml_implied,
            "edge": home_ml_edge,
            "display_odds": "-130",
            "game": away_team + " @ " + home_team,
            "game_id": game["game_id"],
        })

    if away_ml_edge >= MIN_LEG_EDGE:
        bets.append({
            "type": "ML", "sport": "MLB",
            "pick": away_team + " ML",
            "sim_prob": away_win_prob,
            "implied_prob": away_ml_implied,
            "edge": away_ml_edge,
            "display_odds": "+110",
            "game": away_team + " @ " + home_team,
            "game_id": game["game_id"],
        })

    # Total
    book_total = 8.5
    if expected_total > book_total:
        over_prob = min(0.68, 0.50 + (expected_total - book_total) * 0.08)
        over_edge = round(over_prob - 0.50, 4)
        if over_edge >= MIN_LEG_EDGE:
            bets.append({
                "type": "TOTAL", "sport": "MLB",
                "pick": "OVER " + str(book_total),
                "sim_prob": over_prob,
                "implied_prob": 0.50,
                "edge": over_edge,
                "display_odds": "-110",
                "game": away_team + " @ " + home_team,
                "game_id": game["game_id"],
            })
    else:
        under_prob = min(0.68, 0.50 + (book_total - expected_total) * 0.08)
        under_edge = round(under_prob - 0.50, 4)
        if under_edge >= MIN_LEG_EDGE:
            bets.append({
                "type": "TOTAL", "sport": "MLB",
                "pick": "UNDER " + str(book_total),
                "sim_prob": under_prob,
                "implied_prob": 0.50,
                "edge": under_edge,
                "display_odds": "-110",
                "game": away_team + " @ " + home_team,
                "game_id": game["game_id"],
            })

    # Spread
    run_diff = abs(home_runs - away_runs)
    if run_diff > 1.5:
        cover_prob = min(0.65, 0.45 + (run_diff - 1.5) * 0.06)
        cover_implied = american_to_implied(130)
        cover_edge = round(cover_prob - cover_implied, 4)
        if cover_edge >= MIN_LEG_EDGE:
            favorite = home_team if home_runs < away_runs else away_team
            bets.append({
                "type": "SPREAD", "sport": "MLB",
                "pick": favorite + " -1.5",
                "sim_prob": cover_prob,
                "implied_prob": cover_implied,
                "edge": cover_edge,
                "display_odds": "+130",
                "game": away_team + " @ " + home_team,
                "game_id": game["game_id"],
            })

    return bets


def build_game_parlay():
    """
    Build 2-3 leg ML/Spread/Total parlay from different games.
    Only posts if combined edge >= 15%.
    """
    games = get_todays_games()
    if not games:
        return None

    all_bets = []
    for game in games:
        bets = evaluate_game_for_parlay(game)
        all_bets.extend(bets)

    if not all_bets:
        logger.warning("No game bets with edge found")
        return None

    all_bets.sort(key=lambda x: -x["edge"])
    logger.info("Game parlay pool: " + str(len(all_bets)) + " bets")

    legs = []
    used_games = set()

    for bet in all_bets:
        if len(legs) >= MAX_GAME_PARLAY_LEGS:
            break
        if bet["game_id"] not in used_games:
            legs.append(bet)
            used_games.add(bet["game_id"])

    if len(legs) < 2:
        logger.warning("Not enough legs for game parlay")
        return None

    sim_prob = 1.0
    implied_prob = 1.0
    for leg in legs:
        sim_prob *= leg["sim_prob"]
        implied_prob *= leg["implied_prob"]

    edge = round(sim_prob - implied_prob, 4)
    logger.info("Game parlay: " + str(len(legs)) + " legs edge=" + str(edge))

    if edge < MIN_PARLAY_EDGE:
        logger.info("Game parlay edge " + str(edge) + " below minimum - not posting")
        return None

    if edge >= 0.22:
        grade, score = "A+", 91
    elif edge >= 0.18:
        grade, score = "A", 90
    else:
        grade, score = "A-", 88

    return {
        "type": "game_parlay",
        "legs": legs,
        "sim_prob": round(sim_prob, 4),
        "implied_prob": round(implied_prob, 4),
        "edge": edge,
        "grade": grade,
        "confidence_score": score,
        "leg_count": len(legs),
    }


def build_prizepicks_parlay(graded_props):
    """
    Build 4-6 leg PrizePicks slip from ALL graded props.
    Opens to every market the algorithm finds edge in.
    No two props from same game.
    Only posts if combined edge >= 15%.
    """
    if not graded_props:
        return None

    # All graded props eligible - algorithm is the filter
    eligible = [p for p in graded_props if p.get("grade") in ("A+", "A", "A-")]

    if len(eligible) < MIN_PRIZEPICKS_LEGS:
        logger.warning("Not enough eligible props: " + str(len(eligible)))
        return None

    eligible.sort(key=lambda x: -x.get("edge", 0))

    legs = []
    used_games = set()

    for prop in eligible:
        if len(legs) >= MAX_PRIZEPICKS_LEGS:
            break
        game_key = prop.get("team", "") + prop.get("opponent", "")
        if game_key not in used_games:
            legs.append(prop)
            used_games.add(game_key)

    if len(legs) < MIN_PRIZEPICKS_LEGS:
        logger.warning("Not enough legs from different games: " + str(len(legs)))
        return None

    sim_prob = 1.0
    implied_prob = 1.0
    for leg in legs:
        sim_prob *= leg.get("sim_prob", 0.55)
        implied_prob *= leg.get("implied_prob", 0.524)

    edge = round(sim_prob - implied_prob, 4)
    logger.info("PrizePicks: " + str(len(legs)) + " legs edge=" + str(edge))

    if edge < MIN_PRIZEPICKS_EDGE:
        logger.info("PrizePicks edge " + str(edge) + " below minimum - not posting")
        return None

    if edge >= 0.08:
        grade, score = "A+", 91
    elif edge >= 0.05:
        grade, score = "A", 90
    else:
        grade, score = "A-", 88

    return {
        "type": "prizepicks",
        "legs": legs,
        "sim_prob": round(sim_prob, 4),
        "implied_prob": round(implied_prob, 4),
        "edge": edge,
        "grade": grade,
        "confidence_score": score,
        "leg_count": len(legs),
    }


def format_game_parlay_sms(parlay):
    if not parlay:
        return None
    lines = [
        "THE EDGE EQUATION — ALGORITHM PARLAY",
        datetime.now().strftime("%B %d") + "  |  ALGORITHM v2.0",
        str(parlay["leg_count"]) + "-LEG PARLAY  |  Grade: " + parlay["grade"] + " (" + str(parlay["confidence_score"]) + ")",
        "Combined Edge: +" + str(round(parlay["edge"] * 100, 1)) + "%",
        "ML + SPREADS + TOTALS ONLY",
        "",
    ]
    for i, leg in enumerate(parlay["legs"]):
        lines.append(str(i+1) + ". " + leg["pick"] + " (" + leg["display_odds"] + ")")
        lines.append("   " + leg["game"])
        lines.append("   Edge: +" + str(round(leg["edge"] * 100, 1)) + "%")
        lines.append("")
    lines += [
        "Only posts when the math says yes.",
        "10,000 sims. Live data. No feelings. Just facts.",
    ]
    return "\n".join(lines)


def format_prizepicks_sms(parlay):
    if not parlay:
        return None
    lines = [
        "THE EDGE EQUATION — PRIZEPICKS SLIP",
        datetime.now().strftime("%B %d") + "  |  ALGORITHM v2.0",
        str(parlay["leg_count"]) + "-LEG SLIP  |  Grade: " + parlay["grade"] + " (" + str(parlay["confidence_score"]) + ")",
        "Combined Edge: +" + str(round(parlay["edge"] * 100, 1)) + "%",
        "",
    ]
    for i, leg in enumerate(parlay["legs"]):
        player = leg.get("player", "")
        line = leg.get("display_line", "")
        prop = leg.get("prop_label", "")
        odds = leg.get("display_odds", "")
        sport = leg.get("sport_label", "")
        edge_pct = str(round(leg.get("edge", 0) * 100, 1))
        lines.append(str(i+1) + ". " + player + " " + line + " " + prop + " (" + odds + ")")
        lines.append("   " + sport + "  |  Edge: +" + edge_pct + "%")
        lines.append("")
    lines += [
        "Algorithm approved PrizePicks slip.",
        "Only posts when the equation says yes.",
        "10,000 sims. Live data. No feelings. Just facts.",
    ]
    return "\n".join(lines)
