"""
Edge Equation — Manual Scanner
Personal edge finder. No posting. Email only.
Scan any game, prop, or NRFI on demand.
"""
 
import os
import logging
import requests
import numpy as np
from datetime import datetime, timezone
 
logger = logging.getLogger(__name__)
 
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
MC_SIMULATIONS = 10_000
 
SPORT_KEYS = {
    "MLB": "baseball_mlb",
    "NBA": "basketball_nba",
    "NHL": "icehockey_nhl",
    "NFL": "americanfootball_nfl",
    "KBO": "baseball_kbo",
    "NPB": "baseball_npb",
}
 
 
def _american_to_implied(odds: int) -> float:
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)
 
 
def _implied_to_american(prob: float) -> str:
    if prob <= 0 or prob >= 1:
        return "N/A"
    if prob >= 0.5:
        return f"-{round(prob / (1 - prob) * 100)}"
    return f"+{round((1 - prob) / prob * 100)}"
 
 
def _kelly(edge: float, odds: int, fraction: float = 0.125) -> float:
    """Calculate Kelly criterion bet size. Default 1/8 Kelly."""
    if edge <= 0:
        return 0
    if odds > 0:
        b = odds / 100
    else:
        b = 100 / abs(odds)
    p = _american_to_implied(odds)
    q = 1 - p
    k = (b * (p + edge) - q) / b
    return round(max(0, k * fraction), 3)
 
 
def _grade(edge: float) -> str:
    """Internal confidence grade."""
    if edge >= 0.15:
        return "A+"
    elif edge >= 0.10:
        return "A"
    elif edge >= 0.05:
        return "A-"
    return "Below threshold"
 
 
def _fetch_game_odds(sport: str, team_a: str, team_b: str) -> dict | None:
    """Fetch live odds for a specific game."""
    sport_key = SPORT_KEYS.get(sport.upper(), "baseball_mlb")
    try:
        url = f"{ODDS_API_BASE}/sports/{sport_key}/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "totals,h2h,spreads",
            "oddsFormat": "american",
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        games = resp.json()
 
        search = f"{team_a} {team_b}".lower()
        for game in games:
            home = game.get("home_team", "").lower()
            away = game.get("away_team", "").lower()
            if (team_a.lower() in home or team_a.lower() in away or
                    team_b.lower() in home or team_b.lower() in away):
                return game
    except Exception as e:
        logger.warning(f"Odds fetch failed: {e}")
    return None
 
 
def _extract_total(game_data: dict) -> tuple[float, int]:
    """Extract Vegas total and juice from game odds."""
    for bm in game_data.get("bookmakers", []):
        for market in bm.get("markets", []):
            if market.get("key") == "totals":
                for outcome in market.get("outcomes", []):
                    if outcome.get("name") == "Over":
                        return outcome.get("point", 0), outcome.get("price", -110)
    return 0, -110
 
 
def scan_game(sport: str, away: str, home: str,
              proj_away: float, proj_home: float) -> dict:
    """
    Scan a game projection vs Vegas line.
    Returns full analysis for personal use.
    """
    proj_total = round(proj_away + proj_home, 1)
    game_data = _fetch_game_odds(sport, away, home)
 
    if game_data:
        vegas_total, total_juice = _extract_total(game_data)
    else:
        vegas_total = 0
        total_juice = -110
        logger.warning(f"No live odds found for {away} @ {home}")
 
    # Calculate edge
    implied_prob = _american_to_implied(total_juice)
    our_side = "OVER" if proj_total > vegas_total else "UNDER"
 
    # Monte Carlo simulation
    rng = np.random.default_rng()
    sims = rng.poisson(proj_total, MC_SIMULATIONS)
    if our_side == "OVER":
        sim_prob = float(np.mean(sims > vegas_total))
    else:
        sim_prob = float(np.mean(sims < vegas_total))
 
    edge = round(sim_prob - implied_prob, 4)
    kelly_size = _kelly(edge, total_juice)
    grade = _grade(edge)
 
    result = {
        "mode": "game",
        "sport": sport,
        "matchup": f"{away} @ {home}",
        "projection": {
            "away_score": str(proj_away),
            "home_score": str(proj_home),
            "proj_total": str(proj_total),
        },
        "vegas": {
            "total": str(vegas_total),
            "juice": str(total_juice),
            "our_side": our_side,
        },
        "edge": {
            "sim_prob": f"{round(sim_prob * 100, 1)}%",
            "implied_prob": f"{round(implied_prob * 100, 1)}%",
            "edge_percent": f"{round(edge * 100, 1)}%",
            "kelly": f"{kelly_size}u",
            "confidence": grade,
            "qualifies": edge >= 0.05,
        },
        "drivers": [
            f"Projected total: {proj_total}",
            f"Vegas line: {vegas_total} ({our_side})",
            f"Simulation: {round(sim_prob * 100, 1)}% vs implied {round(implied_prob * 100, 1)}%",
            f"Edge: {round(edge * 100, 1)}%",
            f"Kelly: {kelly_size}u (1/8 Kelly)",
        ],
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }
 
    logger.info(f"[SCANNER] Game scan: {away} @ {home} | Edge: {round(edge*100,1)}% | {grade}")
    return result
 
 
def scan_prop(sport: str, player: str, prop_type: str,
              proj_value: float, vegas_line: float,
              vegas_juice: int = -110) -> dict:
    """
    Scan a player prop projection vs Vegas line.
    """
    implied_prob = _american_to_implied(vegas_juice)
    our_side = "OVER" if proj_value > vegas_line else "UNDER"
 
    # Monte Carlo simulation using Poisson for counting stats
    rng = np.random.default_rng()
    sims = rng.poisson(proj_value, MC_SIMULATIONS)
    if our_side == "OVER":
        sim_prob = float(np.mean(sims > vegas_line))
    else:
        sim_prob = float(np.mean(sims < vegas_line))
 
    edge = round(sim_prob - implied_prob, 4)
    kelly_size = _kelly(edge, vegas_juice)
    grade = _grade(edge)
 
    result = {
        "mode": "prop",
        "sport": sport,
        "player": player,
        "prop_type": prop_type,
        "projection": {
            "proj_value": str(proj_value),
            "vegas_line": str(vegas_line),
            "vegas_juice": str(vegas_juice),
            "our_side": our_side,
        },
        "edge": {
            "sim_prob": f"{round(sim_prob * 100, 1)}%",
            "implied_prob": f"{round(implied_prob * 100, 1)}%",
            "edge_percent": f"{round(edge * 100, 1)}%",
            "kelly": f"{kelly_size}u",
            "confidence": grade,
            "qualifies": edge >= 0.05,
        },
        "drivers": [
            f"Projection: {proj_value} {prop_type}",
            f"Vegas line: {vegas_line} ({our_side})",
            f"Simulation: {round(sim_prob * 100, 1)}% vs implied {round(implied_prob * 100, 1)}%",
            f"Edge: {round(edge * 100, 1)}%",
            f"Kelly: {kelly_size}u (1/8 Kelly)",
        ],
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }
 
    logger.info(f"[SCANNER] Prop scan: {player} {prop_type} | Edge: {round(edge*100,1)}% | {grade}")
    return result
 
 
def scan_nrfi(away: str, home: str,
              away_era: float, home_era: float,
              weather_factor: float = 1.0,
              umpire_factor: float = 1.0,
              park_factor: float = 1.0,
              vegas_juice: int = -135) -> dict:
    """
    Scan NRFI probability for a game.
    """
    # Estimate first inning run probability per team
    away_fi_rate = (away_era / 9) * weather_factor * umpire_factor * park_factor
    home_fi_rate = (home_era / 9) * weather_factor * umpire_factor * park_factor
 
    # Monte Carlo
    rng = np.random.default_rng()
    away_sims = rng.poisson(away_fi_rate, MC_SIMULATIONS)
    home_sims = rng.poisson(home_fi_rate, MC_SIMULATIONS)
    nrfi_sims = (away_sims == 0) & (home_sims == 0)
    nrfi_prob = float(np.mean(nrfi_sims))
 
    implied_prob = _american_to_implied(vegas_juice)
    edge = round(nrfi_prob - implied_prob, 4)
    kelly_size = _kelly(edge, vegas_juice)
    grade = _grade(edge)
 
    result = {
        "mode": "nrfi",
        "matchup": f"{away} @ {home}",
        "projection": {
            "nrfi_probability": f"{round(nrfi_prob * 100, 1)}%",
            "away_fi_rate": str(round(away_fi_rate, 3)),
            "home_fi_rate": str(round(home_fi_rate, 3)),
        },
        "vegas": {
            "juice": str(vegas_juice),
            "implied_prob": f"{round(implied_prob * 100, 1)}%",
        },
        "edge": {
            "sim_prob": f"{round(nrfi_prob * 100, 1)}%",
            "edge_percent": f"{round(edge * 100, 1)}%",
            "kelly": f"{kelly_size}u",
            "confidence": grade,
            "qualifies": edge >= 0.05,
        },
        "drivers": [
            f"Away ERA: {away_era} → FI rate: {round(away_fi_rate, 3)}",
            f"Home ERA: {home_era} → FI rate: {round(home_fi_rate, 3)}",
            f"Weather factor: {weather_factor}",
            f"Umpire factor: {umpire_factor}",
            f"Park factor: {park_factor}",
            f"NRFI sim prob: {round(nrfi_prob * 100, 1)}%",
            f"Vegas implied: {round(implied_prob * 100, 1)}%",
            f"Edge: {round(edge * 100, 1)}%",
        ],
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }
 
    logger.info(f"[SCANNER] NRFI scan: {away} @ {home} | {round(nrfi_prob*100,1)}% | Edge: {round(edge*100,1)}%")
    return result
 
 
def format_scan_email(result: dict) -> str:
    """Format scan result for email."""
    mode = result.get("mode", "scan")
    sep = "=" * 50
    lines = [
        "EDGE EQUATION — MANUAL SCAN",
        f"Mode: {mode.upper()}",
        f"Scanned: {result.get('scanned_at', '')}",
        sep,
    ]
 
    if mode == "game":
        lines += [
            f"MATCHUP: {result['matchup']}",
            f"Sport: {result['sport']}",
            "",
            "PROJECTION:",
            f"  Away: {result['projection']['away_score']}",
            f"  Home: {result['projection']['home_score']}",
            f"  Total: {result['projection']['proj_total']}",
            "",
            "VEGAS:",
            f"  Line: {result['vegas']['total']}",
            f"  Juice: {result['vegas']['juice']}",
            f"  Our side: {result['vegas']['our_side']}",
        ]
    elif mode == "prop":
        lines += [
            f"PLAYER: {result['player']}",
            f"PROP: {result['prop_type']}",
            f"Sport: {result['sport']}",
            "",
            "PROJECTION:",
            f"  Projected: {result['projection']['proj_value']}",
            f"  Vegas line: {result['projection']['vegas_line']}",
            f"  Our side: {result['projection']['our_side']}",
        ]
    elif mode == "nrfi":
        lines += [
            f"MATCHUP: {result['matchup']}",
            "",
            "PROJECTION:",
            f"  NRFI probability: {result['projection']['nrfi_probability']}",
        ]
 
    edge = result.get("edge", {})
    lines += [
        "",
        sep,
        "EDGE ANALYSIS:",
        f"  Sim prob: {edge.get('sim_prob', 'N/A')}",
        f"  Implied prob: {edge.get('implied_prob', edge.get('', 'N/A'))}",
        f"  Edge: {edge.get('edge_percent', 'N/A')}",
        f"  Kelly size: {edge.get('kelly', 'N/A')}",
        f"  Confidence: {edge.get('confidence', 'N/A')}",
        f"  Qualifies (>5% edge): {'YES' if edge.get('qualifies') else 'NO'}",
        "",
        sep,
        "DRIVERS:",
    ]
    for driver in result.get("drivers", []):
        lines.append(f"  • {driver}")
 
    lines += [
        "",
        sep,
        "This scan is for personal use only.",
        "Not gambling advice. Not a pick.",
        "No feelings. Just facts.",
    ]
 
    return "\n".join(lines)
 
 
def run_scan_and_email(mode: str, **kwargs) -> bool:
    """Run a scan and email the result."""
    from engine.email_sender import _send
 
    if mode == "game":
        result = scan_game(**kwargs)
    elif mode == "prop":
        result = scan_prop(**kwargs)
    elif mode == "nrfi":
        result = scan_nrfi(**kwargs)
    else:
        logger.error(f"Unknown scan mode: {mode}")
        return False
 
    subject = f"EE MANUAL SCAN — {mode.upper()} | {datetime.now().strftime('%B %d %H:%M')}"
    body = format_scan_email(result)
    return _send(subject, body)
 
 
if __name__ == "__main__":
    import json
 
    # Test game scan
    result = scan_game(
        sport="MLB",
        away="Yankees",
        home="Red Sox",
        proj_away=4.3,
        proj_home=5.6,
    )
    print(format_scan_email(result))
    print()
 
    # Test prop scan
    result = scan_prop(
        sport="MLB",
        player="Gerrit Cole",
        prop_type="Strikeouts",
        proj_value=7.2,
        vegas_line=6.5,
        vegas_juice=-130,
    )
    print(format_scan_email(result))
    print()
 
    # Test NRFI scan
    result = scan_nrfi(
        away="Yankees",
        home="Red Sox",
        away_era=3.2,
        home_era=3.8,
        weather_factor=0.95,
        umpire_factor=1.02,
        park_factor=1.05,
    )
    print(format_scan_email(result))
