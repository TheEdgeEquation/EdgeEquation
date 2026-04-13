import logging
import json
import os
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
BANKROLL_UNITS = 100.0
UNIT_SIZE_USD = 10.0
MAX_SINGLE_BET_UNITS = 2.0
MAX_DAILY_EXPOSURE_UNITS = 5.0
MIN_EDGE_TO_SIZE_UP = 0.08
FLAT_BET_UNITS = 0.5
CALIBRATION_DAYS = 30
BANKROLL_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "bankroll.json")
 
 
def _load_bankroll():
    try:
        if os.path.exists(BANKROLL_FILE):
            with open(BANKROLL_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {"units": BANKROLL_UNITS, "start_date": datetime.now().strftime("%Y-%m-%d"), "total_wagered": 0, "total_won": 0}
 
 
def _save_bankroll(data):
    try:
        os.makedirs(os.path.dirname(BANKROLL_FILE), exist_ok=True)
        with open(BANKROLL_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error("Bankroll save failed: " + str(e))
 
 
def get_days_since_launch():
    try:
        data = _load_bankroll()
        start = datetime.strptime(data.get("start_date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
        return (datetime.now() - start).days
    except Exception:
        return 0
 
 
def get_kelly_fraction():
    days = get_days_since_launch()
    if days < CALIBRATION_DAYS:
        return 0.125
    return 0.25
 
 
def calculate_kelly_units(edge, odds, max_units=None):
    try:
        if odds > 0:
            b = odds / 100.0
        else:
            b = 100.0 / abs(odds)
        if b <= 0 or edge <= 0:
            return FLAT_BET_UNITS
        p = edge + (1 / (1 + b))
        q = 1 - p
        full_kelly = (b * p - q) / b
        full_kelly = max(0, full_kelly)
        fraction = get_kelly_fraction()
        kelly_units = full_kelly * fraction * BANKROLL_UNITS
        kelly_units = round(kelly_units, 1)
        if edge < MIN_EDGE_TO_SIZE_UP:
            return FLAT_BET_UNITS
        cap = max_units if max_units else MAX_SINGLE_BET_UNITS
        kelly_units = min(kelly_units, cap)
        kelly_units = max(kelly_units, FLAT_BET_UNITS)
        logger.info("Kelly: edge=" + str(edge) + " odds=" + str(odds) + " fraction=" + str(fraction) + " units=" + str(kelly_units))
        return kelly_units
    except Exception as e:
        logger.error("Kelly calc failed: " + str(e))
        return FLAT_BET_UNITS
 
 
def calculate_parlay_units(legs):
    try:
        if not legs:
            return FLAT_BET_UNITS
        avg_edge = sum(l.get("edge", 0) for l in legs) / len(legs)
        base_units = calculate_kelly_units(avg_edge, -110)
        parlay_units = round(base_units * 0.5, 1)
        parlay_units = max(parlay_units, 0.5)
        parlay_units = min(parlay_units, 1.0)
        return parlay_units
    except Exception as e:
        logger.error("Parlay Kelly failed: " + str(e))
        return 0.5
 
 
def calculate_parlay_payout(legs, units):
    try:
        multiplier = 1.0
        for leg in legs:
            odds = leg.get("over_odds", leg.get("display_odds", -110))
            if isinstance(odds, str):
                odds = int(odds.replace("+", ""))
            if odds > 0:
                multiplier *= (1 + odds / 100.0)
            else:
                multiplier *= (1 + 100.0 / abs(odds))
        payout = round(units * (multiplier - 1), 2)
        return round(multiplier, 2), payout
    except Exception as e:
        logger.error("Payout calc failed: " + str(e))
        return 1.0, 0.0
 
 
def apply_kelly_to_plays(plays):
    daily_exposure = 0.0
    sized_plays = []
    for play in plays:
        edge = play.get("edge", 0)
        odds = play.get("over_odds", -115)
        units = calculate_kelly_units(edge, odds)
        if daily_exposure + units > MAX_DAILY_EXPOSURE_UNITS:
            units = max(FLAT_BET_UNITS, MAX_DAILY_EXPOSURE_UNITS - daily_exposure)
            units = round(units, 1)
        if units <= 0:
            continue
        daily_exposure += units
        sized_plays.append({**play, "recommended_units": units, "unit_usd": round(units * UNIT_SIZE_USD, 2)})
    logger.info("Daily exposure: " + str(round(daily_exposure, 1)) + "u / " + str(MAX_DAILY_EXPOSURE_UNITS) + "u max")
    return sized_plays
 
 
def update_bankroll(result_plays):
    try:
        data = _load_bankroll()
        for play in result_plays:
            units = play.get("recommended_units", FLAT_BET_UNITS)
            won = play.get("won", False)
            odds = play.get("over_odds", -115)
            data["total_wagered"] = data.get("total_wagered", 0) + units
            if won:
                if odds > 0:
                    profit = units * odds / 100.0
                else:
                    profit = units * 100.0 / abs(odds)
                data["units"] = data.get("units", BANKROLL_UNITS) + profit
                data["total_won"] = data.get("total_won", 0) + profit
            else:
                data["units"] = data.get("units", BANKROLL_UNITS) - units
        _save_bankroll(data)
        logger.info("Bankroll updated: " + str(round(data["units"], 1)) + "u")
        return data
    except Exception as e:
        logger.error("Bankroll update failed: " + str(e))
        return {}
 
 
def get_bankroll_summary():
    try:
        data = _load_bankroll()
        current_units = data.get("units", BANKROLL_UNITS)
        start_units = BANKROLL_UNITS
        profit_units = round(current_units - start_units, 1)
        roi = round((current_units - start_units) / start_units * 100, 1)
        return {
            "current_units": round(current_units, 1),
            "current_usd": round(current_units * UNIT_SIZE_USD, 2),
            "profit_units": profit_units,
            "profit_usd": round(profit_units * UNIT_SIZE_USD, 2),
            "roi_pct": roi,
            "total_wagered": round(data.get("total_wagered", 0), 1),
            "days_active": get_days_since_launch(),
            "kelly_fraction": get_kelly_fraction(),
        }
    except Exception as e:
        logger.error("Bankroll summary failed: " + str(e))
        return {"current_units": BANKROLL_UNITS, "roi_pct": 0.0}
