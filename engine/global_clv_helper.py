import logging

logger = logging.getLogger("global_clv_helper")

def attach_placeholder_clv(game):
    """
    Ensures every global game object has:
    - vegas_total
    - closing_total

    Since The Odds API free tier does NOT provide:
    - KBO totals
    - NPB totals
    - EPL/UCL totals
    - closing line history

    We attach neutral placeholders so the engine stays stable.
    """

    # If the scraper already provided a vegas_total, keep it.
    vegas = game.get("vegas_total")

    # If missing, fall back to model total or total.
    if vegas is None:
        vegas = game.get("model_total") or game.get("total")

    # Attach vegas_total
    game["vegas_total"] = vegas

    # Attach closing_total (neutral placeholder)
    game["closing_total"] = vegas

    return game


def attach_clv_to_list(games):
    """
    Applies placeholder CLV to a list of global games.
    """
    if not games:
        return games

    patched = []
    for g in games:
        try:
            patched.append(attach_placeholder_clv(g))
        except Exception as e:
            logger.error(f"CLV patch failed for game {g}: {e}")
            patched.append(g)

    return patched
