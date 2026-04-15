import logging
from datetime import datetime, date as date_type
from engine.unified_formatter import build_edge_equation_post
 
logger = logging.getLogger(__name__)
 
ALGO_VERSION = "2.0"
 
DAILY_CTA = {
    0: "Follow the build. Week 1 of public calibration.",
    1: "Most models hide their math. We show ours.",
    2: "The algorithm doesn't lie. Neither do we.",
    3: "9 layers of data. 10,000 simulations. Zero opinions.",
    4: "Week 1 results post tomorrow. Follow along.",
    5: "The math is public. Make of it what you will.",
    6: "Week 2 coming. The model is getting sharper.",
}
 
LEAGUE_CONFIG = {
    "MLB": {"full": "Major League Baseball", "hashtag": "MajorLeagueBaseball", "night": True},
    "NBA": {"full": "National Basketball Association", "hashtag": "NBA", "night": True},
    "NHL": {"full": "National Hockey League", "hashtag": "NHL", "night": True},
    "NFL": {"full": "National Football League", "hashtag": "NFL", "night": True},
    "KBO": {"full": "Korean Baseball", "hashtag": "KoreanBaseball", "night": False},
    "NPB": {"full": "Japanese Baseball", "hashtag": "JapaneseBaseball", "night": False},
    "EPL": {"full": "English Premier League", "hashtag": "PremierLeague", "night": False},
    "UCL": {"full": "UEFA Champions League", "hashtag": "ChampionsLeague", "night": False},
}
 
 
def get_daily_cta():
    return DAILY_CTA.get(datetime.now().weekday(), "No feelings. Just facts.")
 
 
def get_mission_line():
    return "This is data. Not advice."
 
 
def _games_to_dicts(projections, home_key="home_team", away_key="away_team",
                    home_score_key="home_runs", away_score_key="away_runs", total_key="total"):
    games = []
    for g in projections:
        home = g.get(home_key, g.get("home_team", ""))
        away = g.get(away_key, g.get("away_team", ""))
        h_score = g.get(home_score_key) or g.get("home_score") or g.get("home_goals") or g.get("home_runs", 0)
        a_score = g.get(away_score_key) or g.get("away_score") or g.get("away_goals") or g.get("away_runs", 0)
        total = g.get(total_key, round(float(h_score) + float(a_score), 1))
        if home and away:
            games.append({
                "team_a": away,
                "team_b": home,
                "a_score": float(a_score),
                "b_score": float(h_score),
                "total": float(total),
            })
    return games
 
 
def generate_mlb_projection_post(projections, max_games=10):
    if not projections:
        return ""
    cfg = LEAGUE_CONFIG["MLB"]
    games = _games_to_dicts(projections[:max_games])
    if not games:
        return ""
    return build_edge_equation_post(
        league_short="MLB",
        league_full_name=cfg["full"],
        algo_version=ALGO_VERSION,
        games=games,
        game_date=datetime.now().date(),
        is_night_slate=True,
        league_full_hashtag=cfg["hashtag"],
    )
 
 
def generate_pitcher_projection_post(pitcher_projections, max_pitchers=8):
    if not pitcher_projections:
        return ""
    date_str = datetime.now().strftime("%B %-d")
    lines = [
        "EDGE EQUATION — MLB PITCHER PROJECTIONS",
        date_str + " | Algorithm v" + ALGO_VERSION,
        "Major League Baseball | Tonight's Slate",
        "",
    ]
    for p in pitcher_projections[:max_pitchers]:
        player = p.get("player", "")
        proj_ks = p.get("projected_ks", 0)
        swstr = p.get("swstr_pct", 0)
        opp = (p.get("opponent", "") or "")[:3].upper()
        lines.append(player + " vs " + opp + ": " + str(proj_ks) + " K projected | SwStr% " + str(swstr) + "%")
    lines += ["", "This is data. Not advice.", "#MLB #MajorLeagueBaseball"]
    return "\n".join(lines)
 
 
def generate_nba_projection_post(projections, player_projections=None, max_games=6):
    if not projections:
        return ""
    cfg = LEAGUE_CONFIG["NBA"]
    games = _games_to_dicts(projections[:max_games],
                            home_score_key="home_score", away_score_key="away_score")
    if not games:
        return ""
    return build_edge_equation_post(
        league_short="NBA",
        league_full_name=cfg["full"],
        algo_version=ALGO_VERSION,
        games=games,
        game_date=datetime.now().date(),
        is_night_slate=True,
        league_full_hashtag=cfg["hashtag"],
    )
 
 
def generate_nhl_projection_post(projections, player_projections=None, max_games=6):
    if not projections:
        return ""
    cfg = LEAGUE_CONFIG["NHL"]
    games = _games_to_dicts(projections[:max_games],
                            home_score_key="home_goals", away_score_key="away_goals")
    if not games:
        return ""
    return build_edge_equation_post(
        league_short="NHL",
        league_full_name=cfg["full"],
        algo_version=ALGO_VERSION,
        games=games,
        game_date=datetime.now().date(),
        is_night_slate=True,
        league_full_hashtag=cfg["hashtag"],
    )
 
 
def generate_kbo_projection_post(projections):
    if not projections:
        return ""
    from datetime import timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    cfg = LEAGUE_CONFIG["KBO"]
    games = _games_to_dicts(projections)
    if not games:
        return ""
    return build_edge_equation_post(
        league_short="KBO",
        league_full_name=cfg["full"],
        algo_version=ALGO_VERSION,
        games=games,
        game_date=tomorrow,
        is_night_slate=False,
        league_full_hashtag=cfg["hashtag"],
    )
 
 
def generate_npb_projection_post(projections):
    if not projections:
        return ""
    from datetime import timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    cfg = LEAGUE_CONFIG["NPB"]
    games = _games_to_dicts(projections)
    if not games:
        return ""
    return build_edge_equation_post(
        league_short="NPB",
        league_full_name=cfg["full"],
        algo_version=ALGO_VERSION,
        games=games,
        game_date=tomorrow,
        is_night_slate=False,
        league_full_hashtag=cfg["hashtag"],
    )
 
 
def generate_epl_projection_post(projections):
    if not projections:
        return ""
    from datetime import timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    cfg = LEAGUE_CONFIG["EPL"]
    games = _games_to_dicts(projections,
                            home_score_key="home_goals", away_score_key="away_goals")
    if not games:
        return ""
    return build_edge_equation_post(
        league_short="EPL",
        league_full_name=cfg["full"],
        algo_version=ALGO_VERSION,
        games=games,
        game_date=tomorrow,
        is_night_slate=False,
        league_full_hashtag=cfg["hashtag"],
    )
 
 
def generate_ucl_projection_post(projections):
    if not projections:
        return ""
    from datetime import timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    cfg = LEAGUE_CONFIG["UCL"]
    games = _games_to_dicts(projections,
                            home_score_key="home_goals", away_score_key="away_goals")
    if not games:
        return ""
    return build_edge_equation_post(
        league_short="UCL",
        league_full_name=cfg["full"],
        algo_version=ALGO_VERSION,
        games=games,
        game_date=tomorrow,
        is_night_slate=False,
        league_full_hashtag=cfg["hashtag"],
    )
 
 
def generate_nrfi_probability_post(nrfi_plays):
    if not nrfi_plays:
        return ""
    date_str = datetime.now().strftime("%B %-d")
    lines = [
        "EDGE EQUATION — FIRST INNING PROBABILITIES",
        date_str + " | Algorithm v" + ALGO_VERSION,
        "Major League Baseball | Tonight's Slate",
        "",
    ]
    shown = set()
    for play in nrfi_plays[:8]:
        team = play.get("team", "")
        opp = play.get("opponent", "")
        key = opp + "@" + team
        if key in shown:
            continue
        shown.add(key)
        nrfi_prob = play.get("sim_prob", 0.6) if play.get("prop_label") == "NRFI" else round(1 - play.get("sim_prob", 0.4), 3)
        yrfi_prob = round(1 - nrfi_prob, 3)
        t = (team.split()[-1] if team else "")[:10]
        o = (opp.split()[-1] if opp else "")[:10]
        lines.append(o + " @ " + t + ": NRFI " + str(round(nrfi_prob * 100, 1)) + "% | YRFI " + str(round(yrfi_prob * 100, 1)) + "%")
    lines += ["", "This is data. Not advice.", "#MLB #MajorLeagueBaseball"]
    return "\n".join(lines)
 
 
def generate_results_post(results, style="ee"):
    if not results:
        return "Results pending.\n\n#EdgeEquation"
    verified = [r for r in results if r.get("result_checked")]
    if not verified:
        return "Results still coming in.\n\n#EdgeEquation"
    wins = sum(1 for r in verified if r.get("won"))
    losses = len(verified) - wins
    date_str = datetime.now().strftime("%B %-d")
    lines = ["EDGE EQUATION — " + date_str + " RESULTS", ""]
    for r in verified[:5]:
        player = r.get("player", "")
        dl = r.get("display_line", "")
        prop = r.get("prop_label", "")
        won = r.get("won")
        actual = r.get("actual_result", "")
        symbol = "✅" if won else "❌"
        actual_str = " | Actual: " + str(actual) if actual else ""
        lines.append(symbol + " " + player + " " + dl + " " + prop + actual_str)
    lines += ["", str(wins) + "-" + str(losses) + " today", ""]
    if wins > losses:
        lines.append("Edge confirmed.")
    elif wins == losses:
        lines.append("Split day. The model keeps running.")
    else:
        lines.append("Tough day. Every result posted.")
    lines += ["", "This is data. Not advice.", "#EdgeEquation"]
    return "\n".join(lines)
 
 
def generate_no_play_post():
    date_str = datetime.now().strftime("%B %-d")
    return "\n".join([
        "EDGE EQUATION — " + date_str,
        "",
        "The model evaluated every available market today.",
        "",
        "No significant edge identified.",
        "",
        "We do not force plays.",
        "We wait for the math.",
        "",
        get_daily_cta(),
        "#EdgeEquation",
    ])
 
 
def generate_weekly_poll():
    return "\n".join([
        "The algorithm ran projections across all sports this week.",
        "",
        "Which breakdown do you want to see?",
        "",
        "MLB — Pitcher model deep dive",
        "NBA — Scoring model breakdown",
        "NHL — SOG model breakdown",
        "KBO — Korean Baseball analysis",
        "",
        get_daily_cta(),
        "#EdgeEquation",
    ])
 
 
def generate_monday_accountability_thread(stats, week_num=1):
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    win_rate = stats.get("win_rate", 0)
    net_units = stats.get("net_units", 0)
    roi = stats.get("roi", 0)
    by_grade = stats.get("by_grade", {})
    prefix = "+" if net_units >= 0 else ""
    lines = [
        "EDGE EQUATION — WEEK " + str(week_num) + " ACCOUNTABILITY",
        datetime.now().strftime("%B %-d, %Y"),
        "",
        "Record: " + str(wins) + "-" + str(losses) + " (" + str(win_rate) + "%)",
        "Net units: " + prefix + str(net_units) + "u",
        "ROI: " + prefix + str(roi) + "%",
        "",
    ]
    for grade in ("A+", "A", "A-"):
        g = by_grade.get(grade, {})
        if g.get("total", 0) > 0:
            lines.append(grade + ": " + str(g["wins"]) + "-" + str(g["total"] - g["wins"]) + " (" + str(g["win_rate"]) + "%)")
    lines += ["", "Every result posted. No exceptions.", "This is data. Not advice.", "#EdgeEquation"]
    return "\n".join(lines)
 
 
def generate_monthly_calibration_thread(stats, month_num=1):
    wins = stats.get("wins", 0)
    total = stats.get("total", 0)
    win_rate = stats.get("win_rate", 0)
    roi = stats.get("roi", 0)
    avg_clv = stats.get("avg_clv", 0)
    by_grade = stats.get("by_grade", {})
    lines = [
        "EDGE EQUATION — MONTH " + str(month_num) + " CALIBRATION",
        datetime.now().strftime("%B %Y"),
        "",
        "Graded plays: " + str(total),
        "Record: " + str(wins) + "-" + str(total - wins) + " (" + str(win_rate) + "%)",
        "ROI: " + ("+" if roi >= 0 else "") + str(roi) + "%",
        "Closing line value: +" + str(avg_clv) + "% avg",
        "",
    ]
    for grade in ("A+", "A", "A-"):
        g = by_grade.get(grade, {})
        if g.get("total", 0) > 0:
            lines.append(grade + ": " + str(g["wins"]) + "-" + str(g["total"] - g["wins"]) + " (" + str(g["win_rate"]) + "%)")
    lines += ["", "The model is learning.", "This is data. Not advice.", "#EdgeEquation"]
    return "\n".join(lines)
 
 
def generate_model_vs_vegas_post(plays):
    if not plays:
        return ""
    date_str = datetime.now().strftime("%B %-d")
    lines = ["EDGE EQUATION — MODEL vs VEGAS", date_str, ""]
    for play in plays[:5]:
        player = play.get("player", "")
        prop = play.get("prop_label", "")
        proj = round(play.get("true_lambda", 0), 1)
        line = play.get("line", 0)
        diff = round(proj - line, 1)
        symbol = "+" if diff >= 0 else ""
        lines.append(player + " " + prop + ": Model " + str(proj) + " | Market " + str(line) + " (" + symbol + str(diff) + ")")
    lines += ["", "We act when the gap is significant.", "This is data. Not advice.", "#EdgeEquation"]
    return "\n".join(lines)
 
 
def generate_weather_alert_post(play, old_weather, new_weather):
    player = play.get("player", "")
    prop = play.get("prop_label", "K")
    return "\n".join([
        "EDGE EQUATION — WEATHER UPDATE",
        datetime.now().strftime("%B %-d"),
        "",
        "Conditions changed at " + (play.get("home_team", "") or "the venue") + ":",
        "Before: " + str(old_weather),
        "After: " + str(new_weather),
        "",
        player + " " + prop + " projection adjusted.",
        "The model updates in real time.",
        "#EdgeEquation",
    ])
 
 
def generate_origin_story_post():
    return "\n".join([
        "EDGE EQUATION",
        "",
        "We built a sports analytics engine from scratch.",
        "",
        "What's inside:",
        "",
        "9-layer MLB pitcher model",
        "Baseball Savant SwStr% integration",
        "Live weather per stadium",
        "Umpire strike zone data",
        "Today's lineup and platoon splits",
        "10,000 Monte Carlo simulations per play",
        "Kelly Criterion bet sizing",
        "NBA / NHL / NFL / KBO / NPB / EPL models",
        "",
        "We are not posting picks yet.",
        "",
        "First we show you the engine works.",
        "Every projection. Every result.",
        "Public. Transparent.",
        "",
        get_daily_cta(),
        "#EdgeEquation",
    ])
