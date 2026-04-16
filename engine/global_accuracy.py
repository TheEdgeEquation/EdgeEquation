import logging

logger = logging.getLogger("global_accuracy")

def evaluate_global_results(plays):
    """
    Evaluates global plays (KBO, NPB, EPL, UCL) for accuracy.
    Expects plays with:
    - sport
    - result ("hit" / "miss")
    """

    if not plays:
        return {
            "total": 0,
            "hits": 0,
            "misses": 0,
            "accuracy": 0.0,
            "by_league": {}
        }

    hits = [p for p in plays if p.get("result") == "hit"]
    misses = [p for p in plays if p.get("result") == "miss"]

    # League breakdown
    leagues = {}
    for p in plays:
        league = p.get("sport")
        if league not in leagues:
            leagues[league] = {"hits": 0, "misses": 0}

        if p.get("result") == "hit":
            leagues[league]["hits"] += 1
        elif p.get("result") == "miss":
            leagues[league]["misses"] += 1

    total = len(plays)
    accuracy = round(len(hits) / total * 100, 2) if total > 0 else 0.0

    return {
        "total": total,
        "hits": len(hits),
        "misses": len(misses),
        "accuracy": accuracy,
        "by_league": leagues,
    }


def generate_global_accuracy_post(stats):
    """
    Generates a clean, premium accuracy post for global markets.
    """

    if stats["total"] == 0:
        return "EDGE EQUATION 3.0 — GLOBAL ACCURACY\n\nNo global plays graded today."

    lines = [
        "EDGE EQUATION 3.0 — GLOBAL ACCURACY",
        "",
        f"Total plays: {stats['total']}",
        f"Hits: {stats['hits']}",
        f"Misses: {stats['misses']}",
        f"Accuracy: {stats['accuracy']}%",
        "",
        "League breakdown:",
    ]

    for league, data in stats["by_league"].items():
        total = data["hits"] + data["misses"]
        acc = round(data["hits"] / total * 100, 2) if total > 0 else 0.0
        lines.append(f"{league.upper()}: {acc}% ({data['hits']}–{data['misses']})")

    lines.append("")
    lines.append("#EdgeEquation")

    return "\n".join(lines)
