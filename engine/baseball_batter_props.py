import logging
from engine.edge_calculator import grade_all_props

logger = logging.getLogger(__name__)


def _default_line(prop_label):
    defaults = {
        "HITS": (1.5, -110, -110, 0.524),
        "TOTAL_BASES": (1.5, -110, -110, 0.524),
        "HOME_RUNS": (0.5, 350, -500, 0.22),
        "RBI": (0.5, -110, -110, 0.524),
        "RUNS": (0.5, -110, -110, 0.524),
    }
    line, over, under, implied = defaults.get(prop_label, (1.0, -110, -110, 0.5))
    return {
        "line": line,
        "over_odds": over,
        "under_odds": under,
        "implied_prob": implied,
    }


def _build_batter_props_for_league(league: str):
    """
    Build raw batter props (hits, TB, HR, RBI, runs) for MLB, KBO, NPB.
    """
    try:
        from engine.stats.lineups import get_today_batters
        from engine.stats.odds_batter import get_batter_prop_lines
    except Exception as e:
        logger.error("Imports failed for " + league + ": " + str(e))
        return []

    batters = get_today_batters(league)
    if not batters:
        return []

    lines = get_batter_prop_lines(league) or {}
    props = []

    sport_code = "baseball_mlb" if league == "MLB" else f"baseball_{league.lower()}"

    for b in batters:
        player = b.get("player", "")
        team = b.get("team", "")
        opponent = b.get("opponent", "")
        commence = b.get("commence_time", "")

        for prop_label in ("HITS", "TOTAL_BASES", "HOME_RUNS", "RBI", "RUNS"):
            key = (player, prop_label)
            line_info = lines.get(key) or _default_line(prop_label)

            props.append(
                {
                    "player": player,
                    "team": team,
                    "opponent": opponent,
                    "sport": sport_code,
                    "sport_label": league,
                    "prop_label": prop_label,
                    "icon": "⚾",
                    "line": line_info["line"],
                    "over_odds": line_info["over_odds"],
                    "under_odds": line_info["under_odds"],
                    "implied_prob": round(line_info["implied_prob"], 4),
                    "source": "model_generated",
                    "commence_time": commence,
                }
            )

    logger.info(f"{league} batter props built: {len(props)}")
    return props


def generate_all_baseball_batter_props():
    """
    Generate and grade all batter props across MLB, KBO, NPB.
    """
    all_props = []
    for league in ("MLB", "KBO", "NPB"):
        all_props.extend(_build_batter_props_for_league(league))

    if not all_props:
        return []

    graded = grade_all_props(all_props)
    return graded
