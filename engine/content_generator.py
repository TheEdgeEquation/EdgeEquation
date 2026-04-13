import logging
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
 
def generate_no_play_post():
    date_str = datetime.now().strftime("%B %d")
    return "\n".join([
        "THE EDGE EQUATION — " + date_str,
        "",
        "The model ran 10,000 simulations",
        "on every available prop today.",
        "",
        "No edge found.",
        "",
        "We don't force plays.",
        "We don't chase action.",
        "We wait for the math.",
        "",
        "Back tomorrow.",
        "",
        "No feelings. Just facts.",
        "#EdgeEquation #NoPlay",
    ])
 
 
def generate_weather_alert_post(play, old_weather, new_weather):
    player = play.get("player", "")
    line = play.get("line", 0)
    prop = play.get("prop_label", "K")
    old_proj = play.get("true_lambda", 0)
    return "\n".join([
        "WEATHER ALERT — MODEL UPDATED",
        datetime.now().strftime("%B %d"),
        "",
        "Conditions changed at " + (play.get("home_team", "") or "the stadium") + ":",
        "Before: " + str(old_weather),
        "After: " + str(new_weather),
        "",
        player + " " + str(line) + " " + prop,
        "Original projection: " + str(round(old_proj, 1)),
        "Updated — play downgraded.",
        "",
        "The model adjusts in real time.",
        "#EdgeEquation #WeatherAlert",
    ])
 
 
def generate_model_vs_vegas_post(plays_with_opening):
    if not plays_with_opening:
        return ""
    date_str = datetime.now().strftime("%B %d")
    lines = ["MODEL vs VEGAS — Opening Lines", date_str, ""]
    lines.append("Our model vs where books opened:")
    lines.append("")
    agreed = 0
    disagreed = 0
    for play in plays_with_opening[:5]:
        player = play.get("player", "")
        prop = play.get("prop_label", "K")
        model_proj = round(play.get("true_lambda", 0), 1)
        book_line = play.get("line", 0)
        diff = model_proj - book_line
        if abs(diff) >= 0.5:
            symbol = "+" if diff > 0 else ""
            lines.append(player + " " + prop + ": Model " + str(model_proj) + " | Book " + str(book_line) + " (" + symbol + str(round(diff, 1)) + ")")
            if diff > 0:
                disagreed += 1
            else:
                agreed += 1
        else:
            lines.append(player + " " + prop + ": Model " + str(model_proj) + " | Book " + str(book_line) + " (aligned)")
            agreed += 1
    lines += ["", "Model disagreed with Vegas on " + str(disagreed) + " of " + str(len(plays_with_opening)) + " lines.", "We only play when the gap is significant.", "", "#EdgeEquation #ModelVsVegas"]
    return "\n".join(lines)
 
 
def generate_weekly_poll():
    return "\n".join([
        "The algorithm found edge across multiple sports this week.",
        "",
        "Which breakdown do you want to see?",
        "",
        "Reply with:",
        "MLB — Pitcher K model",
        "NHL — Shots on goal model",
        "NBA — 3-pointer model",
        "ALL — Show me everything",
        "",
        "#EdgeEquation #AskTheAlgorithm",
    ])
 
 
def generate_monday_accountability_thread(stats, week_num=1):
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    total = stats.get("total", 0)
    win_rate = stats.get("win_rate", 0)
    net_units = stats.get("net_units", 0)
    roi = stats.get("roi", 0)
    by_grade = stats.get("by_grade", {})
    prefix = "+" if net_units >= 0 else ""
    lines = [
        "WEEK " + str(week_num) + " ACCOUNTABILITY THREAD",
        datetime.now().strftime("%B %d, %Y"),
        "",
        "Full transparency. Every play. Every result.",
        "",
        "Record: " + str(wins) + "-" + str(losses) + " (" + str(win_rate) + "%)",
        "Net units: " + prefix + str(net_units) + "u",
        "ROI: " + prefix + str(roi) + "%",
        "",
        "By tier:",
    ]
    for grade in ("A+", "A", "A-"):
        g = by_grade.get(grade, {})
        if g.get("total", 0) > 0:
            lines.append(grade + " TIER: " + str(g["wins"]) + "-" + str(g["total"]-g["wins"]) + " (" + str(g["win_rate"]) + "%)")
    if net_units < 0:
        lines += ["", "Tough week. The model missed some.", "We post every result. Win or lose.", "The edge is real. The variance is real too."]
    else:
        lines += ["", "Solid week. The model found genuine edge.", "Results prove the math."]
    lines += ["", "Full play log available on request.", "No feelings. Just facts.", "#EdgeEquation #Transparency #Results"]
    return "\n".join(lines)
 
 
def generate_monthly_calibration_thread(stats, month_num=1):
    total = stats.get("total", 0)
    wins = stats.get("wins", 0)
    win_rate = stats.get("win_rate", 0)
    roi = stats.get("roi", 0)
    avg_clv = stats.get("avg_clv", 0)
    model_accuracy = stats.get("model_accuracy", 0)
    by_grade = stats.get("by_grade", {})
    lines = [
        "MONTH " + str(month_num) + " MODEL CALIBRATION REPORT",
        datetime.now().strftime("%B %Y"),
        "",
        "Total plays evaluated: RUNNING",
        "Total plays posted: " + str(total),
        "Record: " + str(wins) + "-" + str(total-wins) + " (" + str(win_rate) + "%)",
        "ROI: " + ("+" if roi >= 0 else "") + str(roi) + "%",
        "",
        "By tier:",
    ]
    for grade in ("A+", "A", "A-"):
        g = by_grade.get(grade, {})
        if g.get("total", 0) > 0:
            lines.append(grade + ": " + str(g["wins"]) + "-" + str(g["total"]-g["wins"]) + " (" + str(g["win_rate"]) + "%)")
    lines += [
        "",
        "Closing line value: +" + str(avg_clv) + "% avg",
        "(Model beats closing line = real edge)",
        "",
        "The model is learning.",
        "The edge is real.",
        "",
        "No feelings. Just facts.",
        "#EdgeEquation #Transparency #Calibration",
    ]
    return "\n".join(lines)
 
 
def generate_origin_story_thread():
    tweets = [
        "How we built the sharpest free sports analytics engine on X.\n\nA thread about The Edge Equation.\n\n(1/8)",
        "Most pick services are just opinions dressed up as analysis.\n\nWe built something different.\n\nA real algorithm. Real math. Every result posted.\n\n(2/8)",
        "The model runs 10,000 Monte Carlo simulations on every play.\n\nNot gut feelings. Not hot takes.\n\nPoisson distribution using true expected value.\n\n(3/8)",
        "For MLB pitcher strikeouts we use 9 layers of adjustment:\n\nSwStr% + platoon splits + weather + umpire zone + park factor + altitude + opponent K rate + pitch mix + blended season stats\n\n(4/8)",
        "SwStr% (swinging strike rate) is the single best predictor of strikeouts.\n\nBooks underweight it. We built it into the core model.\n\n(5/8)",
        "We compare our true lambda against book implied probability.\n\nOnly post when edge exceeds our threshold.\n\nNo edge = no play. We never force it.\n\n(6/8)",
        "Every result is posted. Win or lose.\n\nThe track record is public.\n\nThe model is the product. The transparency is the brand.\n\n(7/8)",
        "No feelings. Just facts.\n\nFollow for daily algorithm-approved plays across MLB, NBA, NHL, NFL.\n\nThe Edge Equation.\n\n#EdgeEquation #SportsBetting #Algorithm\n\n(8/8)",
    ]
    return tweets
 
 
def generate_results_post(results, style="ee"):
    if not results:
        return "No results available yet. Games may still be in progress.\n\n#EdgeEquation #Results"
    verified = [r for r in results if r.get("result_checked")]
    if not verified:
        return "Results still coming in. Check back shortly.\n\n#EdgeEquation #Results"
    wins = sum(1 for r in verified if r.get("won"))
    losses = len(verified) - wins
    date_str = datetime.now().strftime("%B %d")
    lines = ["THE EDGE EQUATION — " + date_str + " RESULTS", ""]
    for r in verified:
        player = r.get("player", "")
        display_line = r.get("display_line", "")
        prop = r.get("prop_label", "")
        grade = r.get("grade", "")
        won = r.get("won")
        actual = r.get("actual_result", "")
        symbol = "✅" if won else "❌"
        result_str = " | Actual: " + str(actual) if actual else ""
        lines.append(symbol + " " + player + " " + display_line + " " + prop + " (" + grade + ")" + result_str)
    lines += ["", "Record today: " + str(wins) + "-" + str(losses), ""]
    if wins > losses:
        lines.append("Edge confirmed. The math does not lie.")
    elif wins == losses:
        lines.append("Split day. The model keeps running.")
    else:
        lines.append("Tough day. Every result posted. No hiding.")
    lines += ["", "No feelings. Just facts.", "#EdgeEquation #Results"]
    return "\n".join(lines)
