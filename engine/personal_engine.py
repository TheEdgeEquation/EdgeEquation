import logging
import math
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
MIN_PERSONAL_PARLAY_LEGS = 2
MAX_PERSONAL_PARLAY_LEGS = 4
MIN_PERSONAL_PP_LEGS = 4
MAX_PERSONAL_PP_LEGS = 6
LEAGUE_AVG_ERA = 4.25
LEAGUE_AVG_RUNS = 4.5
 
 
def american_to_implied(odds):
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)
 
 
def build_personal_parlay(game_bets):
    if not game_bets:
        return None
    sorted_bets = sorted(game_bets, key=lambda x: -x.get("edge", 0))
    legs = []
    used_games = set()
    for bet in sorted_bets:
        if len(legs) >= MAX_PERSONAL_PARLAY_LEGS:
            break
        gid = bet.get("game_id", "")
        if gid not in used_games:
            legs.append(bet)
            used_games.add(gid)
    if len(legs) < MIN_PERSONAL_PARLAY_LEGS:
        return None
    sim_prob = 1.0
    implied_prob = 1.0
    for leg in legs:
        sim_prob *= leg.get("sim_prob", 0.55)
        implied_prob *= leg.get("implied_prob", 0.524)
    edge = round(sim_prob - implied_prob, 4)
    multiplier = 1.0
    for leg in legs:
        odds = leg.get("over_odds", leg.get("display_odds", -110))
        if isinstance(odds, str):
            try:
                odds = int(odds.replace("+", ""))
            except Exception:
                odds = -110
        if odds > 0:
            multiplier *= (1 + odds / 100.0)
        else:
            multiplier *= (1 + 100.0 / abs(odds))
    payout_multiplier = round(multiplier, 2)
    logger.info("Personal parlay: " + str(len(legs)) + " legs edge=" + str(edge))
    return {
        "type": "personal_parlay",
        "legs": legs,
        "sim_prob": round(sim_prob, 4),
        "implied_prob": round(implied_prob, 4),
        "edge": edge,
        "leg_count": len(legs),
        "payout_multiplier": payout_multiplier,
    }
 
 
def build_personal_prizepicks(all_graded_props):
    if not all_graded_props:
        return None
    eligible = [p for p in all_graded_props if p.get("grade") in ("A+", "A", "A-")]
    if not eligible:
        eligible = sorted(all_graded_props, key=lambda x: -x.get("edge", 0))
    eligible = sorted(eligible, key=lambda x: -x.get("edge", 0))
    legs = []
    used_games = set()
    for prop in eligible:
        if len(legs) >= MAX_PERSONAL_PP_LEGS:
            break
        game_key = prop.get("team", "") + prop.get("opponent", "")
        if game_key not in used_games:
            legs.append(prop)
            used_games.add(game_key)
    if len(legs) < MIN_PERSONAL_PP_LEGS:
        return None
    power_payouts = {4: 10.0, 5: 20.0, 6: 40.0}
    flex_payouts = {4: 1.5, 5: 2.0, 6: 2.5}
    n = len(legs)
    power_mult = power_payouts.get(n, 10.0)
    flex_mult = flex_payouts.get(n, 1.5)
    logger.info("Personal PrizePicks: " + str(n) + " legs")
    return {
        "type": "personal_prizepicks",
        "legs": legs,
        "leg_count": n,
        "power_play_multiplier": power_mult,
        "flex_play_multiplier": flex_mult,
    }
 
 
def format_personal_parlay_text(parlay, kelly_units=0.5):
    if not parlay:
        return "No personal parlay found today."
    legs = parlay["legs"]
    payout = parlay.get("payout_multiplier", 1.0)
    estimated_win = round(kelly_units * (payout - 1) * 10, 2)
    lines = [
        "YOUR BEST PARLAY TODAY (" + str(parlay["leg_count"]) + " legs)",
        "ML + SPREADS + TOTALS | Personal — not posted",
        "Combined edge: +" + str(round(parlay["edge"] * 100, 1)) + "%",
        "Recommended: " + str(kelly_units) + "u ($" + str(round(kelly_units * 10, 2)) + ")",
        "Est. payout: " + str(payout) + "x ($" + str(estimated_win) + " profit)",
        "",
    ]
    for i, leg in enumerate(legs):
        pick = leg.get("pick", "")
        odds = leg.get("display_odds", "-110")
        game = leg.get("game", "")
        edge = leg.get("edge", 0)
        lines.append(str(i+1) + ". " + pick + " (" + str(odds) + ")")
        lines.append("   " + game + " | Edge: +" + str(round(edge*100, 1)) + "%")
        lines.append("")
    return "\n".join(lines)
 
 
def format_personal_prizepicks_text(slip, kelly_units=0.5):
    if not slip:
        return "No personal PrizePicks slip found today."
    legs = slip["legs"]
    n = slip["leg_count"]
    power = slip["power_play_multiplier"]
    flex = slip["flex_play_multiplier"]
    power_win = round(kelly_units * power * 10, 2)
    flex_win = round(kelly_units * flex * 10, 2)
    lines = [
        "YOUR BEST PRIZEPICKS SLIP (" + str(n) + " legs)",
        "All markets | Personal — not posted",
        "Recommended: " + str(kelly_units) + "u ($" + str(round(kelly_units * 10, 2)) + ")",
        "Power play (" + str(n) + " legs): " + str(power) + "x → $" + str(power_win) + " profit",
        "Flex play (" + str(n) + " legs): " + str(flex) + "x → $" + str(flex_win) + " profit",
        "",
    ]
    for i, leg in enumerate(legs):
        player = leg.get("player", "")
        display_line = leg.get("display_line", "OVER ?")
        prop = leg.get("prop_label", "")
        sport = leg.get("sport_label", "")
        edge = leg.get("edge", 0)
        grade = leg.get("grade", "")
        lines.append(str(i+1) + ". " + player + " " + display_line + " " + prop)
        lines.append("   " + sport + " | " + grade + " | Edge: +" + str(round(edge*100, 1)) + "%")
        lines.append("")
    return "\n".join(lines)
