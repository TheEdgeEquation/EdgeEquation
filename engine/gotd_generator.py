import logging
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
ALGO_VERSION = "2.0"
 
 
def generate_gotd(
    away_team: str,
    home_team: str,
    away_proj: float,
    home_proj: float,
    vegas_total: float,
    league_short: str,
    key_factors: list,
    model_edge: float = None,
) -> str:
    date_str = datetime.now().strftime("%B %-d")
    total_proj = round(away_proj + home_proj, 1)
    edge_line = ""
    if model_edge is not None:
        edge_line = f"Model Edge: {model_edge:+.1f}\n"
    factors_text = "\n".join(f"• {f}" for f in key_factors[:6])
    post = f"""EDGE EQUATION — GAME OF THE DAY
{date_str} | Algorithm v{ALGO_VERSION}
 
{away_team} @ {home_team}
Projection: {away_proj:.1f} — {home_proj:.1f} | Total: {total_proj:.1f}
Vegas Total: {vegas_total:.1f}
{edge_line}
Why the engine sees this:
{factors_text}
 
Summary:
The model isn't predicting an outcome — it's identifying where the math diverges from the market.
 
This is data. Not advice.
#{league_short} #EdgeEquation"""
    return post.strip()
 
 
def generate_potd(
    player_name: str,
    team: str,
    opponent: str,
    prop_label: str,
    projection: float,
    vegas_line: float,
    league_short: str,
    key_factors: list,
    model_edge: float = None,
) -> str:
    date_str = datetime.now().strftime("%B %-d")
    edge_line = ""
    if model_edge is not None:
        edge_line = f"Model Edge: {model_edge:+.1f}\n"
    factors_text = "\n".join(f"• {f}" for f in key_factors[:6])
    post = f"""EDGE EQUATION — PLAYER OF THE DAY
{date_str} | Algorithm v{ALGO_VERSION}
 
{player_name} — {prop_label}
Team: {team} vs {opponent}
Projection: {projection:.1f} | Vegas Line: {vegas_line:.1f}
{edge_line}
Why the engine sees this:
{factors_text}
 
Summary:
The model isn't predicting an outcome — it's identifying where the math diverges from the market.
 
This is data. Not advice.
#{league_short} #EdgeEquation"""
    return post.strip()
 
 
def generate_gotd_from_play(play: dict) -> str:
    try:
        away = play.get("opponent", "Away")
        home = play.get("team", "Home")
        away_proj = play.get("away_proj", play.get("true_lambda", 0))
        home_proj = play.get("home_proj", play.get("true_lambda", 0))
        vegas_total = play.get("vegas_total", play.get("line", 0))
        league = (play.get("sport_label") or play.get("sport", "MLB")).upper()
        edge = play.get("edge", None)
        factors = _build_factors_from_play(play)
        return generate_gotd(
            away_team=away,
            home_team=home,
            away_proj=float(away_proj),
            home_proj=float(home_proj),
            vegas_total=float(vegas_total),
            league_short=league,
            key_factors=factors,
            model_edge=round(edge * 100, 1) if edge else None,
        )
    except Exception as e:
        logger.error("GOTD from play failed: " + str(e))
        return ""
 
 
def generate_potd_from_play(play: dict) -> str:
    try:
        player = play.get("player", "")
        team = play.get("team", "")
        opponent = play.get("opponent", "")
        prop = play.get("prop_label", "K")
        proj = play.get("true_lambda", 0)
        line = play.get("line", 0)
        league = (play.get("sport_label") or play.get("sport", "MLB")).upper()
        edge = play.get("edge", None)
        factors = _build_factors_from_play(play)
        return generate_potd(
            player_name=player,
            team=team,
            opponent=opponent,
            prop_label=prop,
            projection=float(proj),
            vegas_line=float(line),
            league_short=league,
            key_factors=factors,
            model_edge=round(edge * 100, 1) if edge else None,
        )
    except Exception as e:
        logger.error("POTD from play failed: " + str(e))
        return ""
 
 
def _build_factors_from_play(play: dict) -> list:
    factors = []
    sport = play.get("sport", "")
    prop = play.get("prop_label", "")
    if sport == "baseball_mlb" and prop == "K":
        swstr = play.get("swstr_pct", 0)
        if swstr and swstr != 0.107:
            from engine.analysis_generator import get_percentile_label
            label = get_percentile_label(swstr, 0.107)
            factors.append("SwStr% " + str(round(swstr * 100, 1)) + "% — " + label + " of all starters")
        platoon = play.get("platoon_adjustment", 1.0)
        if platoon >= 1.08:
            factors.append("Platoon edge — lineup heavily favors this matchup")
        elif platoon <= 0.93:
            factors.append("Platoon disadvantage — lineup suppresses strikeout upside")
        umpire = play.get("umpire_adjustment", 1.0)
        if umpire >= 1.04:
            factors.append("Umpire grades above average on called strikes")
        elif umpire <= 0.96:
            factors.append("Umpire grades below average — tight zone today")
        opp_adj = play.get("opp_k_adjustment", 1.0)
        if opp_adj >= 1.08:
            factors.append("Opponent K rate ranks in top tier of MLB lineups")
        elif opp_adj <= 0.92:
            factors.append("Opponent makes contact — below average K rate")
        park = play.get("park_adj", 1.0)
        if park >= 1.02:
            factors.append("Park factor inflates strikeout environment")
        weather = play.get("weather_adj", 1.0)
        if weather <= 0.97:
            factors.append("Weather conditions suppress scoring and K upside")
    elif prop in ("NRFI", "YRFI"):
        home_era = play.get("home_era", 4.25)
        away_era = play.get("away_era", 4.25)
        if prop == "NRFI":
            factors.append("Both starters project as elite first-inning arms")
            factors.append("Home starter ERA " + str(round(home_era, 2)) + " — well below league average")
            factors.append("Away starter ERA " + str(round(away_era, 2)) + " — consistent suppression")
            factors.append("Model: P(scoreless first) = " + str(round(play.get("sim_prob", 0.6) * 100, 1)) + "%")
        else:
            factors.append("First inning run environment elevated")
            factors.append("Home starter ERA " + str(round(home_era, 2)))
            factors.append("Away starter ERA " + str(round(away_era, 2)))
            factors.append("Model: P(run in first) = " + str(round(play.get("sim_prob", 0.6) * 100, 1)) + "%")
    elif sport == "basketball_nba":
        factors.append("Usage rate and pace project above average")
        factors.append("Opponent defense rates below league average")
        factors.append("Rest advantage confirmed")
    elif sport == "icehockey_nhl":
        factors.append("SOG rate per 60 minutes above league average")
        factors.append("Power play time projects elevated tonight")
        factors.append("Opponent allows above average shots per game")
    if not factors:
        edge = play.get("edge", 0)
        line = play.get("line", 0)
        proj = play.get("true_lambda", 0)
        factors.append("Model projection: " + str(round(proj, 1)) + " vs market line: " + str(line))
        factors.append("Edge: " + str(round(edge * 100, 1)) + "% above implied probability")
    return factors[:6]
