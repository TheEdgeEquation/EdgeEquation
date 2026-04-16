import logging

from engine.edge_calculator import grade_all_props

logger = logging.getLogger(__name__)


def _default_line(prop_label):
    if prop_label == "HITS":
        return {"line": 1.5, "over_odds": -110, "under_odds": -110, "implied_prob": 0.524}
    if prop_label == "TOTAL_BASES":
        return {"line": 1.5, "over_odds": -110, "under_odds": -110, "implied_prob": 0.524}
    if prop_label == "HOME_RUNS":
        return {"line": 0.5, "over_odds": 350, "under_odds": -500, "implied_prob": 0.22}
    if prop_label == "RBI":
        return {"line": 0.5, "over_odds": -110, "under_odds": -110, "implied_prob": 0.524}
    if prop_label == "RUNS":
        return {"line": 0.5, "over_odds": -110, "under_odds": -110, "implied_prob": 0.524}
    return {"line": 1.0, "over_odds": -110, "under_odds": -110, "implied_prob": 0.5}


def _build_batter_props_for_league(league: str):
    """
    Build raw batter props (hits, TB, HR, RBI, runs) for a given league.
    League: 'MLB', 'KBO', 'NPB'
    """
    try:
        from engine.stats.lineups import get_today_batters
        from engine.stats.odds_batter import get_batter_prop_lines
    except Exception as e:
        logger.error("Batter prop imports failed for " + league + ": " + str(e))
        return []

    batters = get_today_batters(league)
    if not batters:
        logger.info("No batters found for league " + league)
        return []

    lines = get_batter_prop_lines(league) or {}
    props = []

    sport_code = "baseball_mlb" if league == "MLB" else f"baseball_{league.lower()}"

    for b in batters:
        try:
            player = b.get("player", "")
            team = b.get("team", "")
            opponent = b.get("opponent", "")
            commence = b.get("commence_time", "")

            for prop_label in ("HITS", "TOTAL_BASES", "HOME_RUNS", "RBI", "RUNS"):
                key = (player, prop_label)
                line_info = lines.get(key) or _default_line(prop_label)
                line = line_info["line"]
                over_odds = line_info["over_odds"]
                under_odds = line_info["under_odds"]
                implied = line_info["implied_prob"]

                props.append(
                    {
                        "player": player,
                        "team": team,
                        "opponent": opponent,
                        "sport": sport_code,
                        "sport_label": league,
                        "prop_label": prop_label,
                        "icon": "⚾",
                        "line": line,
                        "over_odds": over_odds,
                        "under_odds": under_odds,
                        "implied_prob": round(implied, 4),
                        "source": "model_generated",
                        "commence_time": commence,
                    }
                )
        except Exception as e:
            logger.error("Batter prop build failed for " + b.get("player", "") + ": " + str(e))

    logger.info(league + " batter props built: " + str(len(props)))
    return props


def generate_all_baseball_batter_props():
    """
    Generate and grade all batter props across MLB, KBO, NPB.
    Returns graded, sorted list.
    """
    all_props = []
    for league in ("MLB", "KBO", "NPB"):
        all_props.extend(_build_batter_props_for_league(league))

    if not all_props:
        logger.info("No batter props generated across leagues")
        return []

    graded = grade_all_props(all_props)
    logger.info("Graded batter props: " + str(len(graded)))
    return graded
