import logging

logger = logging.getLogger("global_clv")

def evaluate_global_clv(plays):
    """
    Evaluates CLV (closing line value) for global plays.
    Expects plays with:
    - sport
    - vegas_total (opening)
    - closing_total (closing)
    """

    if not plays:
        return {
            "total": 0,
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "avg_clv": 0.0,
            "by_league": {}
        }

    diffs = []
    leagues = {}

    for p in plays:
        league = p.get("sport")
        if league not in leagues:
            leagues[league] = {"positive": 0, "negative": 0, "neutral": 0, "diffs": []}

        open_line = p.get("vegas_total")
        close_line = p.get("closing_total")

        if open_line is None or close_line is None:
            continue

        diff = round(close_line - open_line, 2)
        diffs.append(diff)
        leagues[league]["diffs"].append(diff)

        if diff < 0:
            leagues[league]["positive"] += 1
        elif diff > 0:
            leagues[league]["negative"] += 1
        else:
            leagues[league]["neutral"] += 1

    avg_clv = round(sum(diffs) / len(diffs), 2) if diffs else 0.0

    # Build league-level summary
    league_summary = {}
    for league, data in leagues.items():
        if not data["diffs"]:
            league_summary[league] = {"avg_clv": 0.0}
            continue
        league_summary[league] = {
            "avg_clv": round(sum(data["diffs"]) / len(data["diffs"]), 2),
            "positive": data["positive"],
            "negative": data["negative"],
            "neutral": data["neutral"],
        }

    return {
        "total": len(diffs),
        "positive": sum(1 for d in diffs if d < 0),
        "negative": sum(1 for d in diffs if d > 0),
        "neutral": sum(1 for d in diffs if d == 0),
        "avg_clv": avg_clv,
        "by_league": league_summary,
    }


def generate_global_clv_post(stats):
    """
    Generates a premium CLV post for global markets.
    """

    if stats["total"] == 0:
        return "EDGE EQUATION 3.0 — GLOBAL CLV\n\nNo global CLV data available."

    lines = [
        "EDGE EQUATION 3.0 — GLOBAL CLV",
        "",
        f"Total graded: {stats['total']}",
        f"Avg CLV: {stats['avg_clv']} pts",
        f"Positive CLV: {stats['positive']}",
        f"Negative CLV: {stats['negative']}",
        f"Neutral: {stats['neutral']}",
        "",
        "League breakdown:",
    ]

    for league, data in stats["by_league"].items():
        lines.append(
            f"{league.upper()}: {data['avg_clv']} pts "
            f"(+{data['positive']} / -{data['negative']} / {data['neutral']} neutral)"
        )

    lines.append("")
    lines.append("#EdgeEquation")

    return "\n".join(lines)
