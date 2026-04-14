import logging
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
DAILY_CTA = {
    0: "Follow the build. Week 1 of public calibration.",
    1: "Most models hide their math. We show ours.",
    2: "The algorithm doesn't lie. Neither do we.",
    3: "9 layers of data. 10,000 simulations. Zero opinions.",
    4: "Week 1 results post tomorrow. Follow along.",
    5: "The math is public. Make of it what you will.",
    6: "Week 2 coming. The model is getting sharper.",
}
 
MISSION_LINES = [
    "This is data. Not advice.",
    "We show the math. You decide.",
    "No picks. Just projections.",
    "Transparent analytics. Real math.",
]
 
 
def get_daily_cta():
    day = datetime.now().weekday()
    return DAILY_CTA.get(day, "Follow the build. No feelings. Just facts.")
 
 
def get_mission_line():
    day = datetime.now().day % len(MISSION_LINES)
    return MISSION_LINES[day]
 
 
def generate_mlb_projection_post(game_projections, max_games=10):
    if not game_projections:
        return ""
    date_str = datetime.now().strftime("%B %d")
    lines = [
        "THE EDGE EQUATION — MLB PROJECTIONS",
        date_str + "  |  Algorithm v2.0  |  10,000 sims per game",
        "",
    ]
    for g in game_projections[:max_games]:
        home = g.get("home_team", "").split()[-1][:3].upper()
        away = g.get("away_team", "").split()[-1][:3].upper()
        home_runs = g.get("home_runs", 0)
        away_runs = g.get("away_runs", 0)
        total = g.get("total", 0)
        dome = g.get("dome", False)
        weather = g.get("weather", "")
        weather_note = " [Dome]" if dome else (" [" + weather + "]" if weather and weather not in ("Clear", "Clouds") else "")
        lines.append(away + " @ " + home + ":  " + str(away_runs) + " — " + str(home_runs) + "  |  Model total: " + str(total) + weather_note)
    lines += [
        "",
        get_mission_line(),
        get_daily_cta(),
        "#EdgeEquation #MLB #BaseballAnalytics",
    ]
    return "\n".join(lines)
 
 
def generate_pitcher_projection_post(pitcher_projections, max_pitchers=8):
    if not pitcher_projections:
        return ""
    date_str = datetime.now().strftime("%B %d")
    lines = [
        "THE EDGE EQUATION — PITCHER PROJECTIONS",
        date_str + "  |  Algorithm v2.0",
        "K/9 + SwStr% + Platoon + Weather + Umpire",
        "",
    ]
    for p in pitcher_projections[:max_pitchers]:
        player = p.get("player", "")
        proj_ks = p.get("projected_ks", 0)
        swstr = p.get("swstr_pct", 0)
        team = (p.get("team", "") or "")[:3].upper()
        opp = (p.get("opponent", "") or "")[:3].upper()
        lines.append(player + ":  " + str(proj_ks) + " Ks projected  |  SwStr% " + str(swstr) + "%  |  " + opp + " @ " + team)
    lines += [
        "",
        get_mission_line(),
        get_daily_cta(),
        "#EdgeEquation #MLB #PitcherProps",
    ]
    return "\n".join(lines)
 
 
def generate_nba_projection_post(game_projections, player_projections=None, max_games=6):
    if not game_projections:
        return ""
    date_str = datetime.now().strftime("%B %d")
    lines = [
        "THE EDGE EQUATION — NBA PROJECTIONS",
        date_str + "  |  Algorithm v2.0  |  10,000 sims per game",
        "",
        "GAME TOTALS:",
    ]
    for g in game_projections[:max_games]:
        home = g.get("home_team", "").split()[-1][:3].upper()
        away = g.get("away_team", "").split()[-1][:3].upper()
        home_score = g.get("home_score", 0)
        away_score = g.get("away_score", 0)
        total = g.get("total", 0)
        lines.append(away + " @ " + home + ":  " + str(away_score) + " — " + str(home_score) + "  |  Total: " + str(total))
    if player_projections:
        lines.append("")
        lines.append("PLAYER PROJECTIONS:")
        for p in player_projections[:5]:
            player = p.get("player", "")
            prop = p.get("prop_label", "PTS")
            proj = p.get("true_lambda", 0)
            lines.append(player + ":  " + str(round(proj, 1)) + " " + prop + " projected")
    lines += [
        "",
        get_mission_line(),
        get_daily_cta(),
        "#EdgeEquation #NBA #BasketballAnalytics",
    ]
    return "\n".join(lines)
 
 
def generate_nhl_projection_post(game_projections, player_projections=None, max_games=6):
    if not game_projections:
        return ""
    date_str = datetime.now().strftime("%B %d")
    lines = [
        "THE EDGE EQUATION — NHL PROJECTIONS",
        date_str + "  |  Algorithm v2.0  |  10,000 sims per game",
        "",
        "GAME TOTALS:",
    ]
    for g in game_projections[:max_games]:
        home = g.get("home_team", "").split()[-1][:3].upper()
        away = g.get("away_team", "").split()[-1][:3].upper()
        home_goals = g.get("home_goals", 0)
        away_goals = g.get("away_goals", 0)
        total = g.get("total", 0)
        lines.append(away + " @ " + home + ":  " + str(away_goals) + " — " + str(home_goals) + "  |  Total: " + str(total))
    if player_projections:
        lines.append("")
        lines.append("SOG PROJECTIONS:")
        for p in player_projections[:5]:
            player = p.get("player", "")
            proj = p.get("true_lambda", 0)
            lines.append(player + ":  " + str(round(proj, 1)) + " SOG projected")
    lines += [
        "",
        get_mission_line(),
        get_daily_cta(),
        "#EdgeEquation #NHL #HockeyAnalytics",
    ]
    return "\n".join(lines)
 
 
def generate_nrfi_probability_post(nrfi_plays):
    if not nrfi_plays:
        return ""
    date_str = datetime.now().strftime("%B %d")
    lines = [
        "THE EDGE EQUATION — FIRST INNING PROBABILITIES",
        date_str + "  |  Algorithm v2.0",
        "Both pitcher ERA + offense + umpire + weather",
        "",
    ]
    shown = set()
    for play in nrfi_plays[:8]:
        team = play.get("team", "")
        opp = play.get("opponent", "")
        game_key = opp + "@" + team
        if game_key in shown:
            continue
        shown.add(game_key)
        nrfi_prob = play.get("sim_prob", 0) if play.get("prop_label") == "NRFI" else round(1 - play.get("sim_prob", 0), 3)
        yrfi_prob = round(1 - nrfi_prob, 3)
        t = team.split()[-1][:3].upper()
        o = opp.split()[-1][:3].upper()
        lines.append(o + " @ " + t + ":  NRFI " + str(round(nrfi_prob*100, 1)) + "%  |  YRFI " + str(round(yrfi_prob*100, 1)) + "%")
    lines += [
        "",
        "Probability only. This is data. Not advice.",
        get_daily_cta(),
        "#EdgeEquation #MLB #NRFI #YRFI",
    ]
    return "\n".join(lines)
 
 
def generate_results_accuracy_post(results, all_time_stats):
    if not results:
        return generate_no_play_post()
    date_str = datetime.now().strftime("%B %d")
    verified = [r for r in results if r.get("result_checked")]
    wins = sum(1 for r in verified if r.get("won"))
    losses = len(verified) - wins
    total = all_time_stats.get("total", 0)
    win_rate = all_time_stats.get("win_rate", 0)
    lines = [
        "THE EDGE EQUATION — " + date_str + " RESULTS",
        "",
    ]
    for r in verified[:5]:
        player = r.get("player", "")
        dl = r.get("display_line", "")
        prop = r.get("prop_label", "")
        won = r.get("won")
        actual = r.get("actual_result", "")
        symbol = "✅" if won else "❌"
        actual_str = " (Actual: " + str(actual) + ")" if actual else ""
        lines.append(symbol + " " + player + " " + dl + " " + prop + actual_str)
    lines += [
        "",
        "Today: " + str(wins) + "-" + str(losses),
        "Running accuracy: " + str(win_rate) + "% (" + str(total) + " projections)",
        "",
        "We show every result. Win or lose.",
        get_daily_cta(),
        "#EdgeEquation #Results #Transparency",
    ]
    return "\n".join(lines)
 
 
def generate_origin_story_post():
    return "\n".join([
        "THE EDGE EQUATION",
        "",
        "We spent 3 days building a sports analytics engine from scratch.",
        "",
        "What's inside:",
        "",
        "* 9-layer MLB pitcher model",
        "* Baseball Savant SwStr% integration",
        "* Live weather per stadium",
        "* Umpire strike zone data",
        "* Today's lineup + platoon splits",
        "* 10,000 Monte Carlo simulations per play",
        "* Kelly Criterion bet sizing",
        "* NBA / NHL / NFL models",
        "",
        "We're not posting picks yet.",
        "",
        "First we show you the engine works.",
        "Every projection. Every result.",
        "Public. Transparent. Honest.",
        "",
        "Follow the build.",
        "",
        "No feelings. Just facts.",
        "#EdgeEquation #BuildingInPublic #SportsBetting",
    ])
 
 
def generate_no_play_post():
    date_str = datetime.now().strftime("%B %d")
    return "\n".join([
        "THE EDGE EQUATION — " + date_str,
        "",
        "The model ran 10,000 simulations",
        "on every available prop today.",
        "",
        "No significant edge found.",
        "",
        "We don't force plays.",
        "We don't chase action.",
        "We wait for the math.",
        "",
        "Back tomorrow.",
        "",
        get_daily_cta(),
        "#EdgeEquation #NoPlay",
    ])
 
 
def generate_weekly_poll():
    return "\n".join([
        "The algorithm ran projections across all sports this week.",
        "",
        "Which breakdown do you want to see?",
        "",
        "Reply with:",
        "MLB — Pitcher K model deep dive",
        "NBA — Scoring model breakdown",
        "NHL — SOG model breakdown",
        "ALL — Show me everything",
        "",
        get_daily_cta(),
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
        "Full transparency. Every projection. Every result.",
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
        lines += ["", "Tough week. The model missed some.", "We post every result. Win or lose."]
    else:
        lines += ["", "Solid week. The math is working."]
    lines += ["", "No feelings. Just facts.", "#EdgeEquation #Transparency #Results"]
    return "\n".join(lines)
 
 
def generate_monthly_calibration_thread(stats, month_num=1):
    total = stats.get("total", 0)
    wins = stats.get("wins", 0)
    win_rate = stats.get("win_rate", 0)
    roi = stats.get("roi", 0)
    avg_clv = stats.get("avg_clv", 0)
    by_grade = stats.get("by_grade", {})
    lines = [
        "MONTH " + str(month_num) + " MODEL CALIBRATION REPORT",
        datetime.now().strftime("%B %Y"),
        "",
        "Total projections: running",
        "Total graded plays: " + str(total),
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
        "",
        "The model is learning.",
        "The edge is real.",
        "",
        "No feelings. Just facts.",
        "#EdgeEquation #Transparency #Calibration",
    ]
    return "\n".join(lines)
 
 
def generate_model_vs_vegas_post(plays_with_opening):
    if not plays_with_opening:
        return ""
    date_str = datetime.now().strftime("%B %d")
    lines = ["MODEL vs VEGAS — Opening Lines", date_str, ""]
    lines.append("Our projections vs where books opened:")
    lines.append("")
    for play in plays_with_opening[:5]:
        player = play.get("player", "")
        prop = play.get("prop_label", "K")
        model_proj = round(play.get("true_lambda", 0), 1)
        book_line = play.get("line", 0)
        diff = model_proj - book_line
        symbol = "+" if diff > 0 else ""
        lines.append(player + " " + prop + ": Model " + str(model_proj) + " | Book " + str(book_line) + " (" + symbol + str(round(diff, 1)) + ")")
    lines += ["", "We only act when the gap is significant.", get_daily_cta(), "#EdgeEquation #ModelVsVegas"]
    return "\n".join(lines)
 
 
def generate_weather_alert_post(play, old_weather, new_weather):
    player = play.get("player", "")
    line = play.get("line", 0)
    prop = play.get("prop_label", "K")
    return "\n".join([
        "WEATHER ALERT — MODEL UPDATED",
        datetime.now().strftime("%B %d"),
        "",
        "Conditions changed at " + (play.get("home_team", "") or "the stadium") + ":",
        "Before: " + str(old_weather),
        "After: " + str(new_weather),
        "",
        player + " " + str(line) + " " + prop + " projection adjusted.",
        "",
        "The model updates in real time.",
        "#EdgeEquation #WeatherAlert",
    ])
 
 
def generate_results_post(results, style="ee"):
    if not results:
        return "Results pending — games may still be in progress.\n\n#EdgeEquation #Results"
    verified = [r for r in results if r.get("result_checked")]
    if not verified:
        return "Results still coming in.\n\n#EdgeEquation #Results"
    wins = sum(1 for r in verified if r.get("won"))
    losses = len(verified) - wins
    date_str = datetime.now().strftime("%B %d")
    lines = ["THE EDGE EQUATION — " + date_str + " RESULTS", ""]
    for r in verified[:5]:
        player = r.get("player", "")
        display_line = r.get("display_line", "")
        prop = r.get("prop_label", "")
        won = r.get("won")
        actual = r.get("actual_result", "")
        symbol = "✅" if won else "❌"
        result_str = " | Actual: " + str(actual) if actual else ""
        lines.append(symbol + " " + player + " " + display_line + " " + prop + result_str)
    lines += ["", str(wins) + "-" + str(losses) + " today", ""]
    if wins > losses:
        lines.append("Edge confirmed.")
    elif wins == losses:
        lines.append("Split day. The model keeps running.")
    else:
        lines.append("Tough day. Every result posted. No hiding.")
    lines += ["", "No feelings. Just facts.", "#EdgeEquation #Results"]
    return "\n".join(lines)
