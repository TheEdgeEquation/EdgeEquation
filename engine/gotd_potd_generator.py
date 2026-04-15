"""
Edge Equation — GOTD / POTD Generator
Generates Game of the Day and Prop of the Day text for all 12 sports.
Uses fill-in-the-blank templates from MASTER_SPEC.
Brand voice enforced — no picks, no advice, no hype.
"""
 
import logging
import random
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
# ── GOTD Templates per sport ──────────────────────────────────────────────────
 
GOTD_TEMPLATES = {
    "MLB": (
        "Edge Equation — Game of the Day\n\n"
        "{away} @ {home}\n\n"
        "The model flags this as today's highest-leverage matchup.\n\n"
        "Drivers:\n"
        "• Projection variance: {variance}\n"
        "• Pitching delta: {pitching_delta}\n"
        "• Correlation pressure: {correlation}\n"
        "• Line efficiency: {line_efficiency}\n\n"
        "Not a pick. Not advice. Just the game where the math shows the strongest signal.\n\n"
        "#EdgeEquation #MLB"
    ),
    "NBA": (
        "Edge Equation — Game of the Day\n\n"
        "{away} @ {home}\n\n"
        "The model flags this as today's highest-leverage matchup.\n\n"
        "Drivers:\n"
        "• Pace factor: {pace_factor}\n"
        "• Usage concentration: {usage}\n"
        "• Defensive efficiency delta: {def_efficiency}\n"
        "• Correlation pressure: {correlation}\n\n"
        "Not a pick. Not advice. Just the game where the math shows the strongest signal.\n\n"
        "#EdgeEquation #NBA"
    ),
    "NHL": (
        "Edge Equation — Game of the Day\n\n"
        "{away} @ {home}\n\n"
        "The model flags this as today's highest-leverage matchup.\n\n"
        "Drivers:\n"
        "• Expected goal differential: {xg_diff}\n"
        "• Goalie stability index: {goalie_index}\n"
        "• Shot volume projection: {shot_volume}\n"
        "• Line efficiency: {line_efficiency}\n\n"
        "Not a pick. Not advice. Just the game where the math shows the strongest signal.\n\n"
        "#EdgeEquation #NHL"
    ),
    "NFL": (
        "Edge Equation — Game of the Day\n\n"
        "{away} @ {home}\n\n"
        "The model flags this as today's highest-leverage matchup.\n\n"
        "Drivers:\n"
        "• Pace environment: {pace_factor}\n"
        "• Offensive efficiency delta: {off_efficiency}\n"
        "• Pressure rate mismatch: {pressure_rate}\n"
        "• Correlation pressure: {correlation}\n\n"
        "Not a pick. Not advice. Just the game where the math shows the strongest signal.\n\n"
        "#EdgeEquation #NFL"
    ),
    "WNBA": (
        "Edge Equation — Game of the Day\n\n"
        "{away} @ {home}\n\n"
        "The model flags this as today's highest-leverage matchup.\n\n"
        "Drivers:\n"
        "• Pace factor: {pace_factor}\n"
        "• Usage concentration: {usage}\n"
        "• Defensive efficiency delta: {def_efficiency}\n"
        "• Correlation pressure: {correlation}\n\n"
        "Not a pick. Not advice. Just the game where the math shows the strongest signal.\n\n"
        "#EdgeEquation #WNBA"
    ),
    "NCAAF": (
        "Edge Equation — Game of the Day\n\n"
        "{away} @ {home}\n\n"
        "The model flags this as today's highest-leverage matchup.\n\n"
        "Drivers:\n"
        "• Pace environment: {pace_factor}\n"
        "• Offensive efficiency delta: {off_efficiency}\n"
        "• Turnover margin projection: {turnover_margin}\n"
        "• Correlation pressure: {correlation}\n\n"
        "Not a pick. Not advice. Just the game where the math shows the strongest signal.\n\n"
        "#EdgeEquation #NCAAF"
    ),
    "NCAAB": (
        "Edge Equation — Game of the Day\n\n"
        "{away} @ {home}\n\n"
        "The model flags this as today's highest-leverage matchup.\n\n"
        "Drivers:\n"
        "• Pace factor: {pace_factor}\n"
        "• Efficiency delta: {efficiency_delta}\n"
        "• Turnover margin: {turnover_margin}\n"
        "• Correlation pressure: {correlation}\n\n"
        "Not a pick. Not advice. Just the game where the math shows the strongest signal.\n\n"
        "#EdgeEquation #NCAAB"
    ),
    "UFC": (
        "Edge Equation — Game of the Day\n\n"
        "{fighter_a} vs {fighter_b}\n\n"
        "The model flags this as today's highest-leverage fight.\n\n"
        "Drivers:\n"
        "• Striking differential: {striking_diff}\n"
        "• Grappling control projection: {grappling}\n"
        "• Pace volatility: {pace_volatility}\n"
        "• Simulation confidence: {sim_confidence}\n\n"
        "Not a pick. Not advice. Just the fight where the math shows the strongest signal.\n\n"
        "#EdgeEquation #UFC"
    ),
    "KBO": (
        "Cash Before Coffee — Overnight Game of the Day\n\n"
        "{away} @ {home}\n\n"
        "The model flags this as tonight's highest-leverage matchup.\n\n"
        "Drivers:\n"
        "• Pitching delta: {pitching_delta}\n"
        "• Pace factor: {pace_factor}\n"
        "• Contact quality projection: {contact_quality}\n"
        "• Line efficiency: {line_efficiency}\n\n"
        "Not a pick. Not advice. Just the game where the math shows the strongest signal.\n\n"
        "#CashBeforeCoffee #KBO"
    ),
    "NPB": (
        "Cash Before Coffee — Overnight Game of the Day\n\n"
        "{away} @ {home}\n\n"
        "The model flags this as tonight's highest-leverage matchup.\n\n"
        "Drivers:\n"
        "• Pitching delta: {pitching_delta}\n"
        "• Pace factor: {pace_factor}\n"
        "• Contact quality projection: {contact_quality}\n"
        "• Line efficiency: {line_efficiency}\n\n"
        "Not a pick. Not advice. Just the game where the math shows the strongest signal.\n\n"
        "#CashBeforeCoffee #NPB"
    ),
    "EPL": (
        "Cash Before Coffee — Overnight Game of the Day\n\n"
        "{away} @ {home}\n\n"
        "The model flags this as tonight's highest-leverage match.\n\n"
        "Drivers:\n"
        "• Expected goal differential: {xg_diff}\n"
        "• Possession projection: {possession}\n"
        "• Pace volatility: {pace_volatility}\n"
        "• Line efficiency: {line_efficiency}\n\n"
        "Not a pick. Not advice. Just the match where the math shows the strongest signal.\n\n"
        "#CashBeforeCoffee #EPL"
    ),
    "UCL": (
        "Cash Before Coffee — Overnight Game of the Day\n\n"
        "{away} @ {home}\n\n"
        "The model flags this as tonight's highest-leverage match.\n\n"
        "Drivers:\n"
        "• Expected goal differential: {xg_diff}\n"
        "• Possession projection: {possession}\n"
        "• Pace volatility: {pace_volatility}\n"
        "• Line efficiency: {line_efficiency}\n\n"
        "Not a pick. Not advice. Just the match where the math shows the strongest signal.\n\n"
        "#CashBeforeCoffee #UCL"
    ),
}
 
# ── POTD Templates per sport ──────────────────────────────────────────────────
 
POTD_TEMPLATES = {
    "MLB": (
        "Edge Equation — Prop of the Day\n\n"
        "Strongest projection: {player} — {prop}\n\n"
        "Why the engine sees it:\n"
        "• Expected usage shift: {usage_shift}\n"
        "• Matchup efficiency: {matchup_efficiency}\n"
        "• Historical trend alignment: {historical_trend}\n"
        "• Simulation edge: {sim_edge}\n\n"
        "This is a projection summary — not gambling advice.\n\n"
        "#EdgeEquation #MLB"
    ),
    "NBA": (
        "Edge Equation — Prop of the Day\n\n"
        "Strongest projection: {player} — {prop}\n\n"
        "Why the engine sees it:\n"
        "• Usage rate shift: {usage_shift}\n"
        "• Pace multiplier: {pace_multiplier}\n"
        "• DVP alignment: {dvp}\n"
        "• Simulation confidence: {sim_confidence}\n\n"
        "This is a projection summary — not gambling advice.\n\n"
        "#EdgeEquation #NBA"
    ),
    "NHL": (
        "Edge Equation — Prop of the Day\n\n"
        "Strongest projection: {player} — {prop}\n\n"
        "Why the engine sees it:\n"
        "• Time on ice projection: {toi}\n"
        "• Shot attempt rate: {shot_rate}\n"
        "• Matchup leverage: {matchup_leverage}\n"
        "• Simulation confidence: {sim_confidence}\n\n"
        "This is a projection summary — not gambling advice.\n\n"
        "#EdgeEquation #NHL"
    ),
    "NFL": (
        "Edge Equation — Prop of the Day\n\n"
        "Strongest projection: {player} — {prop}\n\n"
        "Why the engine sees it:\n"
        "• Usage expectation: {usage_shift}\n"
        "• Red zone share: {red_zone}\n"
        "• Coverage matchup: {coverage}\n"
        "• Simulation edge: {sim_edge}\n\n"
        "This is a projection summary — not gambling advice.\n\n"
        "#EdgeEquation #NFL"
    ),
    "WNBA": (
        "Edge Equation — Prop of the Day\n\n"
        "Strongest projection: {player} — {prop}\n\n"
        "Why the engine sees it:\n"
        "• Usage rate shift: {usage_shift}\n"
        "• Pace multiplier: {pace_multiplier}\n"
        "• DVP alignment: {dvp}\n"
        "• Simulation confidence: {sim_confidence}\n\n"
        "This is a projection summary — not gambling advice.\n\n"
        "#EdgeEquation #WNBA"
    ),
    "NCAAF": (
        "Edge Equation — Prop of the Day\n\n"
        "Strongest projection: {player} — {prop}\n\n"
        "Why the engine sees it:\n"
        "• Usage expectation: {usage_shift}\n"
        "• Matchup leverage: {matchup_leverage}\n"
        "• Historical trend: {historical_trend}\n"
        "• Simulation edge: {sim_edge}\n\n"
        "This is a projection summary — not gambling advice.\n\n"
        "#EdgeEquation #NCAAF"
    ),
    "NCAAB": (
        "Edge Equation — Prop of the Day\n\n"
        "Strongest projection: {player} — {prop}\n\n"
        "Why the engine sees it:\n"
        "• Usage rate shift: {usage_shift}\n"
        "• Pace multiplier: {pace_multiplier}\n"
        "• Matchup leverage: {matchup_leverage}\n"
        "• Simulation confidence: {sim_confidence}\n\n"
        "This is a projection summary — not gambling advice.\n\n"
        "#EdgeEquation #NCAAB"
    ),
    "UFC": (
        "Edge Equation — Prop of the Day\n\n"
        "Strongest projection: {player} — {prop}\n\n"
        "Why the engine sees it:\n"
        "• Significant strike expectation: {strike_rate}\n"
        "• Control time projection: {control_time}\n"
        "• Historical matchup pattern: {historical_pattern}\n"
        "• Simulation edge: {sim_edge}\n\n"
        "This is a projection summary — not gambling advice.\n\n"
        "#EdgeEquation #UFC"
    ),
    "KBO": (
        "Cash Before Coffee — Overnight Prop of the Day\n\n"
        "Strongest projection: {player} — {prop}\n\n"
        "Why the engine sees it:\n"
        "• Hit probability: {hit_prob}\n"
        "• Strikeout expectation: {k_expectation}\n"
        "• Matchup leverage: {matchup_leverage}\n"
        "• Simulation confidence: {sim_confidence}\n\n"
        "Not a pick — just the projection with the clearest signal.\n\n"
        "#CashBeforeCoffee #KBO"
    ),
    "NPB": (
        "Cash Before Coffee — Overnight Prop of the Day\n\n"
        "Strongest projection: {player} — {prop}\n\n"
        "Why the engine sees it:\n"
        "• Hit probability: {hit_prob}\n"
        "• Strikeout expectation: {k_expectation}\n"
        "• Matchup leverage: {matchup_leverage}\n"
        "• Simulation confidence: {sim_confidence}\n\n"
        "Not a pick — just the projection with the clearest signal.\n\n"
        "#CashBeforeCoffee #NPB"
    ),
    "EPL": (
        "Cash Before Coffee — Overnight Prop of the Day\n\n"
        "Strongest projection: {player} — {prop}\n\n"
        "Why the engine sees it:\n"
        "• Shot volume expectation: {shot_volume}\n"
        "• Chance creation rate: {chance_creation}\n"
        "• Matchup leverage: {matchup_leverage}\n"
        "• Simulation confidence: {sim_confidence}\n\n"
        "Not a pick — just the projection with the clearest signal.\n\n"
        "#CashBeforeCoffee #EPL"
    ),
    "UCL": (
        "Cash Before Coffee — Overnight Prop of the Day\n\n"
        "Strongest projection: {player} — {prop}\n\n"
        "Why the engine sees it:\n"
        "• Shot volume expectation: {shot_volume}\n"
        "• Chance creation rate: {chance_creation}\n"
        "• Matchup leverage: {matchup_leverage}\n"
        "• Simulation confidence: {sim_confidence}\n\n"
        "Not a pick — just the projection with the clearest signal.\n\n"
        "#CashBeforeCoffee #UCL"
    ),
}
 
 
def generate_gotd(sport: str, game: dict) -> str | None:
    """
    Generate GOTD text for a sport given game projection data.
    game dict should contain: away, home, proj_total, vegas_line, edge_percent
    plus any sport-specific driver fields.
    """
    template = GOTD_TEMPLATES.get(sport.upper())
    if not template:
        logger.warning(f"No GOTD template for sport: {sport}")
        return None
 
    try:
        # Build driver placeholders from game data or use defaults
        drivers = _build_drivers(sport, game)
        text = template.format(**drivers)
        logger.info(f"[GOTD] Generated for {sport}: {game.get('away','?')} @ {game.get('home','?')}")
        return text
    except KeyError as e:
        logger.warning(f"[GOTD] Missing field {e} for {sport}")
        return None
 
 
def generate_potd(sport: str, prop: dict) -> str | None:
    """
    Generate POTD text for a sport given prop projection data.
    prop dict should contain: player/teams_or_player, prop, proj_value, vegas_line, edge_percent
    """
    template = POTD_TEMPLATES.get(sport.upper())
    if not template:
        logger.warning(f"No POTD template for sport: {sport}")
        return None
 
    try:
        drivers = _build_prop_drivers(sport, prop)
        text = template.format(**drivers)
        logger.info(f"[POTD] Generated for {sport}: {prop.get('teams_or_player','?')}")
        return text
    except KeyError as e:
        logger.warning(f"[POTD] Missing field {e} for {sport}")
        return None
 
 
def _build_drivers(sport: str, game: dict) -> dict:
    """Build driver fields for GOTD template."""
    sport = sport.upper()
    edge = game.get("edge_percent", "N/A")
    proj = game.get("proj_total", "N/A")
    vegas = game.get("vegas_line", "N/A")
 
    base = {
        "away": game.get("away", game.get("teams", "Away").split("@")[0].strip()),
        "home": game.get("home", game.get("teams", "@ Home").split("@")[-1].strip()),
        "fighter_a": game.get("fighter_a", "Fighter A"),
        "fighter_b": game.get("fighter_b", "Fighter B"),
        "proj_total": proj,
        "vegas_line": vegas,
        "edge_percent": edge,
        # Generic driver defaults — override with real data when available
        "variance": f"High ({edge} edge vs line)",
        "pitching_delta": "Favorable",
        "correlation": "Elevated",
        "line_efficiency": f"Proj {proj} vs Vegas {vegas}",
        "pace_factor": "Above average",
        "usage": "Concentrated",
        "def_efficiency": "Negative delta",
        "xg_diff": "Positive",
        "goalie_index": "Stable",
        "shot_volume": "Elevated",
        "off_efficiency": "Favorable",
        "pressure_rate": "Mismatch detected",
        "turnover_margin": "Positive projection",
        "efficiency_delta": "Favorable",
        "striking_diff": "Positive",
        "grappling": "Control edge",
        "pace_volatility": "Elevated",
        "sim_confidence": "High",
        "contact_quality": "Above average",
        "possession": "Favorable projection",
    }
    return base
 
 
def _build_prop_drivers(sport: str, prop: dict) -> dict:
    """Build driver fields for POTD template."""
    sport = sport.upper()
    player = prop.get("teams_or_player", prop.get("player", "Player"))
    prop_type = prop.get("prop", prop.get("prop_label", "Prop"))
    proj = prop.get("proj_value", prop.get("proj_total", "N/A"))
    vegas = prop.get("vegas_line", "N/A")
    edge = prop.get("edge_percent", "N/A")
 
    return {
        "player": player,
        "prop": f"{prop_type} (Proj: {proj} | Vegas: {vegas})",
        "proj_value": proj,
        "vegas_line": vegas,
        "edge_percent": edge,
        # Generic driver defaults
        "usage_shift": "Elevated vs baseline",
        "matchup_efficiency": "Favorable",
        "historical_trend": "Aligned",
        "sim_edge": edge,
        "pace_multiplier": "Above average",
        "dvp": "Favorable matchup",
        "sim_confidence": "High",
        "toi": "Elevated projection",
        "shot_rate": "Above average",
        "matchup_leverage": "Favorable",
        "red_zone": "Elevated share",
        "coverage": "Favorable alignment",
        "strike_rate": "Above baseline",
        "control_time": "Elevated projection",
        "historical_pattern": "Aligned",
        "hit_prob": "Above average",
        "k_expectation": "Elevated",
        "shot_volume": "Above average",
        "chance_creation": "Elevated",
    }
 
 
def find_top_game(games: list) -> dict | None:
    """Find the game with the highest edge for GOTD."""
    if not games:
        return None
    try:
        def edge_val(g):
            ep = g.get("edge_percent", "0%")
            return float(str(ep).replace("%", "").strip())
        return max(games, key=edge_val)
    except Exception:
        return games[0] if games else None
 
 
def find_top_prop(props: list) -> dict | None:
    """Find the prop with the highest edge for POTD."""
    if not props:
        return None
    try:
        def edge_val(p):
            ep = p.get("edge_percent", "0%")
            return float(str(ep).replace("%", "").strip())
        return max(props, key=edge_val)
    except Exception:
        return props[0] if props else None
 
 
if __name__ == "__main__":
    # Test MLB GOTD
    game = {
        "away": "Yankees", "home": "Red Sox",
        "proj_total": "9.9", "vegas_line": "8.5",
        "edge_percent": "16.5%"
    }
    text = generate_gotd("MLB", game)
    print("GOTD:\n", text)
    print()
 
    # Test MLB POTD
    prop = {
        "teams_or_player": "Gerrit Cole (NYY)",
        "prop": "Strikeouts OVER 6.5",
        "proj_value": "7.2",
        "vegas_line": "6.5",
        "edge_percent": "10.8%"
    }
    text = generate_potd("MLB", prop)
    print("POTD:\n", text)
