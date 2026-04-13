calculator.py
Sharp MLB strikeout + NRFI/YRFI model.
Uses real stats, weather, umpire, and park factors.
Runs 10,000 Poisson Monte Carlo simulations using TRUE lambda.
"""
import numpy as np
import logging
from config.settings import MC_SIMULATIONS, GRADE_THRESHOLDS, NRFI_IMPLIED, YRFI_IMPLIED

logger = logging.getLogger(__name__)


def _format_odds(odds: int) -> str:
    return f"+{odds}" if odds > 0 else str(odds)


def run_monte_carlo(lam: float, line: float) -> float:
    rng = np.random.default_rng()
    draws = rng.poisson(lam=max(lam, 0.1), size=MC_SIMULATIONS)
    over_hits = np.sum(draws > line)
    return round(float(over_hits) / MC_SIMULATIONS, 4)


def assign_grade(edge: float) -> tuple | None:
    for grade, threshold, score, label in GRADE_THRESHOLDS:
        if edge >= threshold:
            return grade, score, label
    return None


def calculate_true_lambda_mlb(prop: dict) -> float:
    try:
        from engine.stats.mlb_stats import get_full_pitcher_profile
        from engine.stats.weather import get_weather
        from engine.stats.umpire import get_umpire_for_game
        from engine.stats.park_factors import get_k_factor, get_altitude_adjustment

        player = prop.get("player", "")
        home_team = prop.get("team", "")
        away_team = prop.get("opponent", "")

        profile = get_full_pitcher_profile(player, away_team, home_team)

        k9_season = profile.get("k9_season", 8.0)
        k9_recent = profile.get("k9_recent", k9_season)
        avg_ip = profile.get("avg_ip_recent", 5.5)

        k9_blended = (k9_recent * 0.60) + (k9_season * 0.40)
        base_lambda = (k9_blended / 9.0) * avg_ip
        logger.info(f"{player}: K/9={k9_blended:.2f}, IP={avg_ip}, base={base_lambda:.2f}")

        opp_adj     = profile.get("opp_k_adjustment", 1.0)
        weather     = get_weather(home_team)
        weather_adj = weather.get("k_adjustment", 1.0)
        umpire_name, umpire_adj = get_umpire_for_game(home_team, away_team)
        park_adj    = get_k_factor(home_team)
        alt_adj     = get_altitude_adjustment(home_team)

        true_lambda = base_lambda * opp_adj * weather_adj * umpire_adj * park_adj * alt_adj
        logger.info(f"True lambda={true_lambda:.3f} (opp={opp_adj}, wx={weather_adj}, ump={umpire_adj}, park={park_adj}, alt={alt_adj})")
        return round(true_lambda, 3)

    except Exception as e:
        logger.error(f"True lambda failed: {e} — using line fallback")
        return max(prop.get("line", 5.0), 0.1)


def calculate_edge(prop: dict) -> dict | None:
    sport = prop.get("sport", "")
    line  = prop.get("line", 0.0)
    implied_prob = prop.get("implied_prob", 0.5)

    if sport == "baseball_mlb":
        lam = calculate_true_lambda_mlb(prop)
    else:
        lam = max(line, 0.1)

    sim_prob = run_monte_carlo(lam, line)
    edge = round(sim_prob - implied_prob, 4)

    grade_result = assign_grade(edge)
    if grade_result is None:
        return None

    grade, score, play_label = grade_result

    return {
        **prop,
        "true_lambda": lam,
        "sim_prob": sim_prob,
        "edge": edge,
        "grade": grade,
        "confidence_score": score,
        "play_label": play_label,
        "display_line": f"OVER {line}",
        "display_odds": _format_odds(prop.get("over_odds", -110)),
    }


def calculate_nrfi_plays(style: str = "ee") -> list[dict]:
    """
    # Fetch todays MLB games and calculate NRFI/YRFI probabilities
    compare against typical book lines, and return graded plays.
    """
    try:
        from engine.stats.nrfi import calculate_nrfi_probability, grade_nrfi
        from engine.stats.weather import get_weather
        from engine.stats.umpire import get_umpire_for_game
        from engine.stats.park_factors import get_k_factor, is_dome
        import requests
        from datetime import datetime

        logger.info("Fetching today's MLB games for NRFI/YRFI...")

        url = "https://statsapi.mlb.com/api/v1/schedule"
        params = {
            "sportId": 1,
            "hydrate": "probablePitcher,team",
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        nrfi_plays = []

        for date in data.get("dates", []):
            for game in date.get("games", []):
                try:
                    home = game.get("teams", {}).get("home", {})
                    away = game.get("teams", {}).get("away", {})

                    home_team = home.get("team", {}).get("name", "")
                    away_team = away.get("team", {}).get("name", "")

                    home_pitcher = home.get("probablePitcher", {}).get("fullName", "")
                    away_pitcher = away.get("probablePitcher", {}).get("fullName", "")

                    if not home_pitcher or not away_pitcher:
                        logger.warning(f"Missing probable pitcher for {away_team} @ {home_team}")
                        continue

                    logger.info(f"NRFI: {away_pitcher} ({away_team}) @ {home_pitcher} ({home_team})")

                    # Get adjustments
                    weather = get_weather(home_team)
                    weather_adj = weather.get("k_adjustment", 1.0)
                    umpire_name, umpire_adj = get_umpire_for_game(home_team, away_team)
                    park_factor = get_k_factor(home_team)

                    # Calculate NRFI probability
                    result = calculate_nrfi_probability(
                        home_pitcher=home_pitcher,
                        away_pitcher=away_pitcher,
                        home_team=home_team,
                        away_team=away_team,
                        umpire_adj=umpire_adj,
                        weather_adj=weather_adj,
                        park_k_factor=park_factor,
                    )

                    nrfi_prob = result["nrfi_prob"]
                    yrfi_prob = result["yrfi_prob"]

                    # Grade NRFI
                    nrfi_edge = round(nrfi_prob - NRFI_IMPLIED, 4)
                    yrfi_edge = round(yrfi_prob - YRFI_IMPLIED, 4)

                    nrfi_grade = assign_grade(nrfi_edge)
                    yrfi_grade = assign_grade(yrfi_edge)

                    commence = game.get("gameDate", "")

                    if nrfi_grade:
                        grade, score, label = nrfi_grade
                        nrfi_plays.append({
                            "player": f"{away_pitcher} / {home_pitcher}",
                            "team": home_team,
                            "opponent": away_team,
                            "sport": "baseball_mlb",
                            "sport_label": "MLB",
                            "prop_label": "NRFI",
                            "icon": "⚾",
                            "line": 0.5,
                            "over_odds": -135,
                            "under_odds": 115,
                            "implied_prob": NRFI_IMPLIED,
                            "sim_prob": nrfi_prob,
                            "edge": nrfi_edge,
                            "grade": grade,
                            "confidence_score": score,
                            "play_label": label,
                            "display_line": "NRFI",
                            "display_odds": "-135",
                            "true_lambda": nrfi_prob,
                            "commence_time": commence,
                            "umpire": umpire_name,
                            "weather": weather.get("condition", ""),
                            "dome": is_dome(home_team),
                        })
                        logger.info(f"NRFI PLAY: {away_team} @ {home_team} — {grade} ({score}) edge={nrfi_edge}")

                    if yrfi_grade:
                        grade, score, label = yrfi_grade
                        nrfi_plays.append({
                            "player": f"{away_pitcher} / {home_pitcher}",
                            "team": home_team,
                            "opponent": away_team,
                            "sport": "baseball_mlb",
                            "sport_label": "MLB",
                            "prop_label": "YRFI",
                            "icon": "⚾",
                            "line": 0.5,
                            "over_odds": 115,
                            "under_odds": -135,
                            "implied_prob": YRFI_IMPLIED,
                            "sim_prob": yrfi_prob,
                            "edge": yrfi_edge,
                            "grade": grade,
                            "confidence_score": score,
                            "play_label": label,
                            "display_line": "YRFI",
                            "display_odds": "+115",
                            "true_lambda": yrfi_prob,
                            "commence_time": commence,
                            "umpire": umpire_name,
                            "weather": weather.get("condition", ""),
                            "dome": is_dome(home_team),
                        })
                        logger.info(f"YRFI PLAY: {away_team} @ {home_team} — {grade} ({score}) edge={yrfi_edge}")

                except Exception as e:
                    logger.error(f"NRFI calc failed for game: {e}")
                    continue

        logger.info(f"NRFI/YRFI: {len(nrfi_plays)} plays found")
        return nrfi_plays

    except Exception as e:
        logger.error(f"NRFI pipeline failed: {e}")
        return []


def grade_all_props(props: list[dict]) -> list[dict]:
    graded = []
    for prop in props:
        result = calculate_edge(prop)
        if result:
            graded.append(result)

    grade_order = {"A+": 0, "A": 1, "A-": 2}
    graded.sort(key=lambda x: (grade_order.get(x["grade"], 9), -x["edge"]))

    logger.info(f"Graded: {len(graded)} of {len(props)} passed threshold")
    return graded
