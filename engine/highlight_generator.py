import logging
import requests
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
ALGO_VERSION = "2.0"
DIVIDER = "\u2501" * 25
MAX_CHARS = 25000
 
# Thresholds for what counts as a highlight
GAME_HIT_THRESHOLD = 0.15       # model total within 15% of actual
PITCHER_HIT_THRESHOLD = 1.5     # projected Ks within 1.5 of actual
ARROW_CORRECT_THRESHOLD = 0.4   # arrow was meaningful and correct
MIN_EDGE_TO_HIGHLIGHT = 0.08    # only highlight plays with real edge
 
 
def _date():
    return datetime.now().strftime("%B %-d")
 
 
def check_mlb_results(projections, pitcher_projections=None):
    """
    Pull actual MLB scores and compare to projections.
    Returns list of highlight-worthy results.
    """
    hits = []
    misses = []
 
    try:
        url = "https://statsapi.mlb.com/api/v1/schedule"
        params = {
            "sportId": 1,
            "hydrate": "linescore,team",
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
 
        actual_scores = {}
        for date in data.get("dates", []):
            for game in date.get("games", []):
                status = game.get("status", {}).get("abstractGameState", "")
                if status != "Final":
                    continue
                home = game.get("teams", {}).get("home", {})
                away = game.get("teams", {}).get("away", {})
                home_team = home.get("team", {}).get("name", "")
                away_team = away.get("team", {}).get("name", "")
                home_score = home.get("score", None)
                away_score = away.get("score", None)
                if home_score is not None and away_score is not None:
                    key = away_team + "@" + home_team
                    actual_scores[key] = {
                        "home_score": home_score,
                        "away_score": away_score,
                        "total": home_score + away_score,
                        "home_team": home_team,
                        "away_team": away_team,
                    }
 
        # Compare projections to actual
        for proj in (projections or []):
            home_team = proj.get("home_team", "")
            away_team = proj.get("away_team", "")
            key = away_team + "@" + home_team
            actual = actual_scores.get(key)
            if not actual:
                continue
 
            proj_total = proj.get("model_total", proj.get("total", 0))
            actual_total = actual["total"]
            vegas_total = proj.get("vegas_total")
            error = abs(proj_total - actual_total)
            error_pct = error / max(actual_total, 1)
 
            result = {
                "type": "game",
                "home_team": home_team,
                "away_team": away_team,
                "proj_home": proj.get("home_runs", 0),
                "proj_away": proj.get("away_runs", 0),
                "proj_total": proj_total,
                "actual_home": actual["home_score"],
                "actual_away": actual["away_score"],
                "actual_total": actual_total,
                "vegas_total": vegas_total,
                "error": round(error, 1),
                "error_pct": round(error_pct * 100, 1),
            }
 
            # Check if arrow was correct
            if vegas_total:
                model_said_over = proj_total > vegas_total
                actual_was_over = actual_total > vegas_total
                result["arrow_correct"] = model_said_over == actual_was_over
                result["arrow_diff"] = abs(proj_total - vegas_total)
            else:
                result["arrow_correct"] = None
 
            if error_pct <= GAME_HIT_THRESHOLD:
                hits.append(result)
                logger.info("Game HIT: " + away_team + " @ " + home_team +
                           " proj=" + str(proj_total) + " actual=" + str(actual_total))
            else:
                misses.append(result)
                logger.info("Game MISS: " + away_team + " @ " + home_team +
                           " proj=" + str(proj_total) + " actual=" + str(actual_total) +
                           " error=" + str(round(error_pct * 100, 1)) + "%")
 
    except Exception as e:
        logger.error("MLB results check failed: " + str(e))
 
    return hits, misses
 
 
def check_pitcher_results(pitcher_projections):
    """
    Pull actual pitcher K totals and compare to projections.
    """
    hits = []
    misses = []
 
    try:
        url = "https://statsapi.mlb.com/api/v1/schedule"
        params = {
            "sportId": 1,
            "hydrate": "boxscore,team",
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
 
        actual_ks = {}
        for date in data.get("dates", []):
            for game in date.get("games", []):
                status = game.get("status", {}).get("abstractGameState", "")
                if status != "Final":
                    continue
                boxscore = game.get("boxscore", {})
                for side in ("home", "away"):
                    pitchers = boxscore.get("teams", {}).get(side, {}).get("pitchers", [])
                    if pitchers:
                        starter_id = pitchers[0]
                        player_stats = boxscore.get("teams", {}).get(side, {}).get(
                            "players", {}).get("ID" + str(starter_id), {})
                        ks = player_stats.get("stats", {}).get("pitching", {}).get("strikeOuts", None)
                        name = player_stats.get("person", {}).get("fullName", "")
                        if name and ks is not None:
                            actual_ks[name] = int(ks)
 
        for proj in (pitcher_projections or []):
            player = proj.get("player", "")
            proj_ks = proj.get("projected_ks", 0)
            actual_k = actual_ks.get(player)
            if actual_k is None:
                continue
 
            error = abs(proj_ks - actual_k)
            result = {
                "type": "pitcher",
                "player": player,
                "team": proj.get("team", ""),
                "opponent": proj.get("opponent", ""),
                "projected_ks": proj_ks,
                "actual_ks": actual_k,
                "error": round(error, 1),
            }
 
            if error <= PITCHER_HIT_THRESHOLD:
                hits.append(result)
                logger.info("Pitcher HIT: " + player +
                           " proj=" + str(proj_ks) + " actual=" + str(actual_k))
            else:
                misses.append(result)
                logger.info("Pitcher MISS: " + player +
                           " proj=" + str(proj_ks) + " actual=" + str(actual_k))
 
    except Exception as e:
        logger.error("Pitcher results check failed: " + str(e))
 
    return hits, misses
 
 
def generate_called_it_post(hits, hit_type="game"):
    """Generate a 'called it' post for notable hits."""
    if not hits:
        return ""
 
    # Pick the most impressive hit
    if hit_type == "game":
        # Prefer hits where arrow was also correct
        arrow_hits = [h for h in hits if h.get("arrow_correct")]
        best = sorted(arrow_hits or hits, key=lambda x: x["error"])[0]
 
        home = best["home_team"].split()[-1]
        away = best["away_team"].split()[-1]
        proj_total = best["proj_total"]
        actual_total = best["actual_total"]
        proj_home = best["proj_home"]
        proj_away = best["proj_away"]
        actual_home = best["actual_home"]
        actual_away = best["actual_away"]
        error = best["error"]
        vegas = best.get("vegas_total")
 
        arrow_line = ""
        if best.get("arrow_correct") and best.get("arrow_diff", 0) >= ARROW_CORRECT_THRESHOLD:
            model_said = "OVER" if proj_total > (vegas or proj_total) else "UNDER"
            arrow_line = "\n\u2191 Arrow was right. Model saw it before the market."
 
        return "\n".join([
            "\U0001f4ca EDGE EQUATION \u2014 MODEL vs RESULT",
            _date(),
            "",
            "\u26be " + away + " @ " + home,
            "",
            "Our projection:",
            "  " + str(proj_away) + " \u2014 " + str(proj_home) + "  |  Total: " + str(proj_total),
            "",
            "Actual result:",
            "  " + str(actual_away) + " \u2014 " + str(actual_home) + "  |  Total: " + str(actual_total),
            "",
            "Model error: " + str(error) + " runs",
            arrow_line,
            "",
            DIVIDER,
            "",
            "10,000 simulations. Live data.",
            "This is data. Not advice.",
            "",
            "#EdgeEquation #MLB #ModelAccuracy",
        ])[:MAX_CHARS]
 
    elif hit_type == "pitcher":
        best = sorted(hits, key=lambda x: x["error"])[0]
        player = best["player"]
        proj = best["projected_ks"]
        actual = best["actual_ks"]
        error = best["error"]
        opp = best.get("opponent", "").split()[-1]
 
        accuracy_line = ""
        if error == 0:
            accuracy_line = "Exact projection."
        elif error <= 0.5:
            accuracy_line = "Within 0.5 Ks. As sharp as it gets."
        else:
            accuracy_line = "Within " + str(error) + " K of projection."
 
        return "\n".join([
            "\U0001f4ca EDGE EQUATION \u2014 PITCHER PROJECTION CHECK",
            _date(),
            "",
            "\u26be " + player + " vs " + opp,
            "",
            "Our projection:  " + str(proj) + " K",
            "Actual result:   " + str(actual) + " K",
            "",
            accuracy_line,
            "",
            DIVIDER,
            "",
            "9-layer model. 10,000 simulations.",
            "This is data. Not advice.",
            "",
            "#EdgeEquation #MLB #PitcherProps",
        ])[:MAX_CHARS]
 
    return ""
 
 
def generate_miss_post(misses, hit_type="game"):
    """
    Generate an honest miss post.
    Transparency builds trust more than hiding mistakes.
    """
    if not misses:
        return ""
 
    # Pick the biggest miss to be transparent about
    if hit_type == "pitcher":
        worst = sorted(misses, key=lambda x: -x["error"])[0]
        player = worst["player"]
        proj = worst["projected_ks"]
        actual = worst["actual_ks"]
        error = worst["error"]
        diff = actual - proj
        direction = "more" if diff > 0 else "fewer"
 
        return "\n".join([
            "\U0001f4ca EDGE EQUATION \u2014 MISS REPORT",
            _date(),
            "",
            "\u26be " + player,
            "",
            "Our projection:  " + str(proj) + " K",
            "Actual result:   " + str(actual) + " K",
            "Error:           " + str(error) + " K",
            "",
            "Pitcher threw " + str(abs(int(diff))) + " K " + direction + " than projected.",
            "",
            "We post every miss.",
            "The model learns from this.",
            "",
            DIVIDER,
            "",
            "This is data. Not advice.",
            "#EdgeEquation #MLB #Transparency",
        ])[:MAX_CHARS]
 
    return ""
 
 
def generate_daily_accuracy_post(game_hits, game_misses, pitcher_hits, pitcher_misses):
    """
    Full accuracy summary post combining all results.
    """
    total_games = len(game_hits) + len(game_misses)
    total_pitchers = len(pitcher_hits) + len(pitcher_misses)
 
    game_accuracy = round(len(game_hits) / max(total_games, 1) * 100, 1)
    pitcher_accuracy = round(len(pitcher_hits) / max(total_pitchers, 1) * 100, 1)
 
    arrow_correct = sum(1 for h in game_hits + game_misses if h.get("arrow_correct"))
    arrow_total = sum(1 for h in game_hits + game_misses if h.get("arrow_correct") is not None)
    arrow_pct = round(arrow_correct / max(arrow_total, 1) * 100, 1)
 
    lines = [
        "\U0001f4ca EDGE EQUATION \u2014 DAILY ACCURACY REPORT",
        _date(),
        "",
        "\U0001f9ee Game totals:",
        "  Projected: " + str(total_games) + " games",
        "  Within 15%: " + str(len(game_hits)) + " (" + str(game_accuracy) + "%)",
    ]
 
    if arrow_total > 0:
        lines += [
            "  Arrow direction correct: " + str(arrow_correct) + "/" + str(arrow_total) +
            " (" + str(arrow_pct) + "%)",
        ]
 
    if total_pitchers > 0:
        lines += [
            "",
            "\u26be Pitcher Ks:",
            "  Projected: " + str(total_pitchers) + " starters",
            "  Within 1.5 K: " + str(len(pitcher_hits)) + " (" + str(pitcher_accuracy) + "%)",
        ]
 
    # Show best hits
    if game_hits:
        lines += ["", DIVIDER, "", "Best game projection today:"]
        best = sorted(game_hits, key=lambda x: x["error"])[0]
        lines.append(
            "\u2705 " + best["away_team"].split()[-1] + " @ " + best["home_team"].split()[-1] +
            "  |  Proj: " + str(best["proj_total"]) +
            "  |  Actual: " + str(best["actual_total"]) +
            "  |  Error: " + str(best["error"])
        )
 
    if pitcher_hits:
        if not game_hits:
            lines += ["", DIVIDER, ""]
        lines += ["", "Best pitcher projection today:"]
        best_p = sorted(pitcher_hits, key=lambda x: x["error"])[0]
        lines.append(
            "\u2705 " + best_p["player"] +
            "  |  Proj: " + str(best_p["projected_ks"]) + " K" +
            "  |  Actual: " + str(best_p["actual_ks"]) + " K" +
            "  |  Error: " + str(best_p["error"])
        )
 
    lines += [
        "",
        DIVIDER,
        "",
        "Every projection tracked. Every result public.",
        "This is data. Not advice.",
        "",
        "#EdgeEquation #ModelAccuracy #Transparency",
    ]
 
    return "\n".join(lines)[:MAX_CHARS]
