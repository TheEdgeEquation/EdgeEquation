import logging
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
ALGO_VERSION = "2.0"
MAX_CHARS = 25000  # X Premium limit
 
DIVIDER = "\u2501" * 25
 
SPORT_EMOJI = {
    "baseball_mlb": "\u26be",
    "basketball_nba": "\U0001f3c0",
    "icehockey_nhl": "\U0001f3d2",
    "americanfootball_nfl": "\U0001f3c8",
    "KBO": "\u26be",
    "NPB": "\u26be",
    "EPL": "\u26bd",
    "UCL": "\u26bd",
    "MLB": "\u26be",
    "NBA": "\U0001f3c0",
    "NHL": "\U0001f3d2",
    "NFL": "\U0001f3c8",
}
 
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
    "MLB": {"full": "Major League Baseball", "hashtag": "MajorLeagueBaseball"},
    "NBA": {"full": "National Basketball Association", "hashtag": "NBA"},
    "NHL": {"full": "National Hockey League", "hashtag": "NHL"},
    "NFL": {"full": "National Football League", "hashtag": "NFL"},
    "KBO": {"full": "Korean Baseball", "hashtag": "KoreanBaseball"},
    "NPB": {"full": "Japanese Baseball", "hashtag": "JapaneseBaseball"},
    "EPL": {"full": "English Premier League", "hashtag": "PremierLeague"},
    "UCL": {"full": "UEFA Champions League", "hashtag": "ChampionsLeague"},
}
 
 
def get_daily_cta():
    return DAILY_CTA.get(datetime.now().weekday(), "No feelings. Just facts.")
 
 
def _short(team):
    return (team or "").split()[-1] if team else ""
 
 
def _emoji(league):
    return SPORT_EMOJI.get(league, "\U0001f4ca")
 
 
def _indicator(model_total, vegas_total, threshold=0.4):
    if vegas_total is None:
        return ""
    diff = model_total - vegas_total
    if diff >= threshold:
        return " \u2191"
    elif diff <= -threshold:
        return " \u2193"
    return " ~"
 
 
def _date():
    return datetime.now().strftime("%B %-d")
 
 
def _footer(league_short, extra_tag=None):
    cfg = LEAGUE_CONFIG.get(league_short, {})
    hashtag = cfg.get("hashtag", league_short)
    tags = ["#EdgeEquation", "#" + league_short]
    if extra_tag:
        tags.append("#" + extra_tag)
    elif hashtag != league_short:
        tags.append("#" + hashtag)
    return "\n".join(["This is data. Not advice.", " ".join(tags)])
 
 
def _build_game_post(league_short, slate_type, games,
                     home_score_key="home_runs",
                     away_score_key="away_runs"):
    if not games:
        return ""
    emoji = _emoji(league_short)
    cfg = LEAGUE_CONFIG.get(league_short, {})
    full_name = cfg.get("full", league_short)
    lines = [
        "\U0001f4ca EDGE EQUATION \u2014 " + league_short + " PROJECTIONS",
        _date() + " | Algorithm v" + ALGO_VERSION,
        full_name + " | " + slate_type,
        "",
    ]
    for g in games:
        h = float(g.get(home_score_key) or g.get("home_score") or
                  g.get("home_goals") or g.get("home_runs") or 0)
        a = float(g.get(away_score_key) or g.get("away_score") or
                  g.get("away_goals") or g.get("away_runs") or 0)
        vt = g.get("vegas_total")
        mt = round(a + h, 1)
        dt = vt if vt is not None else mt
        ind = _indicator(mt, vt)
        away_name = g.get("away_team", "")
        home_name = g.get("home_team", "")
        lines.append(
            emoji + " " + away_name + " @ " + home_name +
            ":  " + f"{a:.1f} \u2014 {h:.1f}" +
            "  |  Line: " + f"{dt:.1f}" + ind
        )
    lines += ["", DIVIDER, "", _footer(league_short), ""]
    return "\n".join(lines)[:MAX_CHARS]
 
 
def generate_mlb_projection_post(projections, max_games=None):
    return _build_game_post("MLB", "Tonight's Slate", projections or [])
 
 
def generate_nba_projection_post(projections, player_projections=None, max_games=None):
    return _build_game_post("NBA", "Tonight's Slate", projections or [],
                             "home_score", "away_score")
 
 
def generate_nhl_projection_post(projections, player_projections=None, max_games=None):
    return _build_game_post("NHL", "Tonight's Slate", projections or [],
                             "home_goals", "away_goals")
 
 
def generate_kbo_projection_post(projections):
    return _build_game_post("KBO", "Tomorrow's Slate", projections or [])
 
 
def generate_npb_projection_post(projections):
    return _build_game_post("NPB", "Tomorrow's Slate", projections or [])
 
 
def generate_epl_projection_post(projections):
    return _build_game_post("EPL", "Tomorrow's Slate", projections or [],
                             "home_goals", "away_goals")
 
 
def generate_ucl_projection_post(projections):
    return _build_game_post("UCL", "Tomorrow's Slate", projections or [],
                             "home_goals", "away_goals")
 
 
def generate_pitcher_projection_post(pitcher_projections, max_pitchers=None):
    if not pitcher_projections:
        return ""
    lines = [
        "\U0001f4ca EDGE EQUATION \u2014 PITCHER PROJECTIONS",
        _date() + " | Algorithm v" + ALGO_VERSION,
        "Major League Baseball | Tonight's Slate",
        "",
    ]
    for p in (pitcher_projections or []):
        player = p.get("player", "")
        proj_ks = p.get("projected_ks", 0)
        swstr = p.get("swstr_pct", 0)
        opp = p.get("opponent", "")
        lines.append(
            "\u26be " + player + " vs " + opp +
            ":  " + str(proj_ks) + " K projected" +
            ("  |  SwStr% " + str(swstr) + "%" if swstr else "")
        )
    lines += ["", DIVIDER, "", _footer("MLB"), ""]
    return "\n".join(lines)[:MAX_CHARS]
 
 
def generate_nrfi_probability_post(nrfi_plays):
    if not nrfi_plays:
        return ""
    lines = [
        "\U0001f4ca EDGE EQUATION \u2014 FIRST INNING PROBABILITIES",
        _date() + " | Algorithm v" + ALGO_VERSION,
        "Major League Baseball | Tonight's Slate",
        "",
        "Model inputs: pitcher ERA + offense + umpire + weather",
        "",
    ]
    shown = set()
    for play in nrfi_plays:
        team = play.get("team", "")
        opp = play.get("opponent", "")
        key = opp + "@" + team
        if key in shown:
            continue
        shown.add(key)
        nrfi_prob = (play.get("sim_prob", 0.6) if play.get("prop_label") == "NRFI"
                     else round(1 - play.get("sim_prob", 0.4), 3))
        yrfi_prob = round(1 - nrfi_prob, 3)
        home_era = play.get("home_era", "")
        away_era = play.get("away_era", "")
        pitcher_info = ""
        if home_era and away_era:
            pitcher_info = "  |  ERAs: " + str(round(away_era, 2)) + " / " + str(round(home_era, 2))
        lines.append(
            "\u26be " + opp + " @ " + team +
            ":  NRFI " + str(round(nrfi_prob * 100, 1)) +
            "%  |  YRFI " + str(round(yrfi_prob * 100, 1)) + "%" +
            pitcher_info
        )
    lines += ["", DIVIDER, "", _footer("MLB"), ""]
    return "\n".join(lines)[:MAX_CHARS]
 
 
def generate_system_status_post():
    return "\n".join([
        "\U0001f4ca EDGE EQUATION \u2014 " + _date(),
        "",
        "\U0001f9ee System online.",
        "Scanning today's full slate:",
        "",
        "\u26be MLB  \U0001f3c0 NBA  \U0001f3d2 NHL  \U0001f3c8 NFL",
        "\U0001f30d KBO  NPB  EPL  UCL",
        "",
        "What we scan:",
        "  \u26be Pitcher strikeouts | 9-layer model",
        "  \u26be NRFI / YRFI probabilities",
        "  \u26be Game totals vs Vegas lines",
        "  \U0001f3c0 Player props | Usage + pace + defense",
        "  \U0001f3d2 Shots on goal | SOG/60 + ice time",
        "  \U0001f30d Overseas markets | KBO NPB EPL UCL",
        "",
        "Game of the Day and Player of the Day",
        "drop before projections.",
        "",
        DIVIDER,
        "",
        get_daily_cta(),
        "",
        "#EdgeEquation #SportsAnalytics",
    ])[:MAX_CHARS]
 
 
def generate_results_post(results, style="ee"):
    if not results:
        return "Results pending.\n\n#EdgeEquation"
    verified = [r for r in results if r.get("result_checked")]
    if not verified:
        return "Results still coming in.\n\n#EdgeEquation"
    wins = sum(1 for r in verified if r.get("won"))
    losses = len(verified) - wins
    win_rate = round(wins / len(verified) * 100, 1) if verified else 0
    lines = [
        "\U0001f4ca EDGE EQUATION \u2014 " + _date() + " RESULTS",
        "",
    ]
    for r in verified:
        player = r.get("player", "")
        dl = r.get("display_line", "")
        prop = r.get("prop_label", "")
        won = r.get("won")
        actual = r.get("actual_result", "")
        grade = r.get("grade", "")
        symbol = "\u2705" if won else "\u274c"
        actual_str = "  |  Actual: " + str(actual) if actual else ""
        grade_str = "  |  " + grade if grade else ""
        lines.append(symbol + " " + player + " " + dl + " " + prop + grade_str + actual_str)
    lines += [
        "",
        DIVIDER,
        "",
        "\U0001f4c8 Today: " + str(wins) + "-" + str(losses) + " (" + str(win_rate) + "%)",
        "",
    ]
    if wins > losses:
        lines.append("Edge confirmed.")
    elif wins == losses:
        lines.append("Split day. The model keeps running.")
    else:
        lines.append("Tough day. Every result posted. No hiding.")
    lines += [
        "",
        "This is data. Not advice.",
        "#EdgeEquation #Results",
    ]
    return "\n".join(lines)[:MAX_CHARS]
 
 
def generate_no_play_post():
    return "\n".join([
        "\U0001f4ca EDGE EQUATION \u2014 " + _date(),
        "",
        "\U0001f9ee The model evaluated every available market.",
        "",
        "No significant edge identified today.",
        "",
        "Markets evaluated:",
        "  \u26be MLB pitcher strikeouts",
        "  \u26be NRFI / YRFI",
        "  \U0001f3c0 NBA player props",
        "  \U0001f3d2 NHL shots on goal",
        "  \U0001f30d Overseas markets",
        "",
        "We do not force plays.",
        "We wait for the math.",
        "",
        DIVIDER,
        "",
        get_daily_cta(),
        "",
        "#EdgeEquation",
    ])[:MAX_CHARS]
 
 
def generate_weekly_poll():
    return "\n".join([
        "\U0001f4ca EDGE EQUATION \u2014 WEEKLY POLL",
        "",
        "The algorithm ran projections across all sports this week.",
        "Which breakdown do you want to see?",
        "",
        "\u26be MLB \u2014 Pitcher model deep dive",
        "\U0001f3c0 NBA \u2014 Scoring model breakdown",
        "\U0001f3d2 NHL \u2014 SOG model breakdown",
        "\U0001f30d KBO \u2014 Korean Baseball analysis",
        "ALL \u2014 Show me everything",
        "",
        DIVIDER,
        "",
        get_daily_cta(),
        "",
        "#EdgeEquation #SportsAnalytics",
    ])[:MAX_CHARS]
 
 
def generate_monday_accountability_thread(stats, week_num=1):
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    win_rate = stats.get("win_rate", 0)
    net_units = stats.get("net_units", 0)
    roi = stats.get("roi", 0)
    by_grade = stats.get("by_grade", {})
    by_sport = stats.get("by_sport", {})
    prefix = "+" if net_units >= 0 else ""
    lines = [
        "\U0001f4ca EDGE EQUATION \u2014 WEEK " + str(week_num) + " ACCOUNTABILITY",
        _date(),
        "",
        "\U0001f4c8 Record: " + str(wins) + "-" + str(losses) + " (" + str(win_rate) + "%)",
        "Net units: " + prefix + str(net_units) + "u",
        "ROI: " + prefix + str(roi) + "%",
        "",
        DIVIDER,
        "",
        "By grade:",
    ]
    for grade in ("A+", "A", "A-"):
        g = by_grade.get(grade, {})
        if g.get("total", 0) > 0:
            lines.append(
                "  " + grade + ": " + str(g["wins"]) + "-" +
                str(g["total"] - g["wins"]) + " (" + str(g["win_rate"]) + "%)"
            )
    if by_sport:
        lines += ["", "By sport:"]
        for sport, data in by_sport.items():
            if data.get("total", 0) > 0:
                lines.append(
                    "  " + sport + ": " + str(data["wins"]) + "-" +
                    str(data["total"] - data["wins"]) + " (" + str(data["win_rate"]) + "%)"
                )
    lines += [
        "",
        DIVIDER,
        "",
        "Every result posted. No exceptions.",
        "This is data. Not advice.",
        "",
        "#EdgeEquation #Transparency",
    ]
    return "\n".join(lines)[:MAX_CHARS]
 
 
def generate_monthly_calibration_thread(stats, month_num=1):
    wins = stats.get("wins", 0)
    total = stats.get("total", 0)
    win_rate = stats.get("win_rate", 0)
    roi = stats.get("roi", 0)
    avg_clv = stats.get("avg_clv", 0)
    model_accuracy = stats.get("model_accuracy", 0)
    by_grade = stats.get("by_grade", {})
    by_sport = stats.get("by_sport", {})
    lines = [
        "\U0001f4ca EDGE EQUATION \u2014 MONTH " + str(month_num) + " CALIBRATION REPORT",
        datetime.now().strftime("%B %Y"),
        "",
        "\U0001f9ee Total projections evaluated: running",
        "\U0001f9ee Total graded plays: " + str(total),
        "\U0001f4c8 Record: " + str(wins) + "-" + str(total - wins) + " (" + str(win_rate) + "%)",
        "ROI: " + ("+" if roi >= 0 else "") + str(roi) + "%",
        "Avg closing line value: +" + str(avg_clv) + "%",
        "",
        DIVIDER,
        "",
        "By grade:",
    ]
    for grade in ("A+", "A", "A-"):
        g = by_grade.get(grade, {})
        if g.get("total", 0) > 0:
            lines.append(
                "  " + grade + ": " + str(g["wins"]) + "-" +
                str(g["total"] - g["wins"]) + " (" + str(g["win_rate"]) + "%)"
            )
    if by_sport:
        lines += ["", "By sport:"]
        for sport, data in by_sport.items():
            if data.get("total", 0) > 0:
                lines.append(
                    "  " + sport + ": " + str(data["wins"]) + "-" +
                    str(data["total"] - data["wins"]) + " (" + str(data["win_rate"]) + "%)"
                )
    lines += [
        "",
        DIVIDER,
        "",
        "The model is learning.",
        "The edge is real.",
        "",
        "This is data. Not advice.",
        "",
        "#EdgeEquation #Transparency #Calibration",
    ]
    return "\n".join(lines)[:MAX_CHARS]
 
 
def generate_model_vs_vegas_post(plays):
    if not plays:
        return ""
    lines = [
        "\U0001f4ca EDGE EQUATION \u2014 MODEL vs VEGAS",
        _date(),
        "",
        "\U0001f9ee Our projections vs opening lines:",
        "",
    ]
    for play in plays:
        player = play.get("player", "")
        prop = play.get("prop_label", "")
        proj = round(play.get("true_lambda", 0), 1)
        line = play.get("line", 0)
        diff = round(proj - line, 1)
        ind = " \u2191" if diff >= 0.4 else (" \u2193" if diff <= -0.4 else " ~")
        prefix = "+" if diff >= 0 else ""
        lines.append(
            "\u26be " + player + " " + prop +
            ":  Model " + str(proj) +
            "  |  Market " + str(line) +
            "  (" + prefix + str(diff) + ")" + ind
        )
    lines += [
        "",
        DIVIDER,
        "",
        "We act when the gap is significant.",
        "This is data. Not advice.",
        "",
        "#EdgeEquation #ModelVsVegas",
    ]
    return "\n".join(lines)[:MAX_CHARS]
 
 
def generate_origin_story_post():
    return "\n".join([
        "\U0001f4ca EDGE EQUATION",
        "",
        "We built a sports analytics engine from scratch.",
        "",
        DIVIDER,
        "",
        "What's inside:",
        "",
        "\u26be 9-layer MLB pitcher model",
        "   K/9 blended + SwStr% + platoon splits",
        "   weather + umpire + park + altitude",
        "   opponent K rate + pitch mix",
        "",
        "\U0001f9ee Baseball Savant SwStr% integration",
        "   Swinging strike rate is the single best",
        "   predictor of strikeouts. Books underweight it.",
        "   We built it into the core model.",
        "",
        "\U0001f9ee Live weather per stadium",
        "   OpenWeatherMap API. Real time.",
        "   Temperature and wind affect run environment.",
        "",
        "\U0001f9ee Umpire strike zone data",
        "   HP umpire grades above or below average.",
        "   Small but consistent signal.",
        "",
        "\U0001f9ee Lineup and platoon splits",
        "   Today's lineup handedness vs pitcher.",
        "   Not last year's data. Today's.",
        "",
        "\U0001f9ee 10,000 Monte Carlo simulations",
        "   Poisson distribution.",
        "   Edge = sim probability minus implied probability.",
        "",
        "\U0001f9ee Kelly Criterion bet sizing",
        "   Eighth Kelly during calibration.",
        "   Quarter Kelly after 30 days proven.",
        "",
        "\U0001f3c0 NBA player props",
        "   Usage + pace + opponent defense + rest",
        "",
        "\U0001f3d2 NHL shots on goal",
        "   SOG/60 + ice time + PP time + opponent",
        "",
        "\U0001f30d KBO / NPB / EPL / UCL overnight",
        "   The algorithm runs while America sleeps.",
        "",
        DIVIDER,
        "",
        "We are not posting picks yet.",
        "",
        "First we show you the engine works.",
        "Every projection. Every result. Public.",
        "Including the misses.",
        "",
        get_daily_cta(),
        "",
        "#EdgeEquation #BuildingInPublic #SportsAnalytics",
    ])[:MAX_CHARS]
 
 
def generate_weather_alert_post(play, old_weather, new_weather):
    player = play.get("player", "")
    prop = play.get("prop_label", "K")
    home_team = play.get("home_team", "the venue")
    return "\n".join([
        "\U0001f4ca EDGE EQUATION \u2014 WEATHER UPDATE",
        _date(),
        "",
        "Conditions changed at " + home_team + ":",
        "",
        "Before: " + str(old_weather),
        "After:  " + str(new_weather),
        "",
        "\u26be " + player + " " + prop + " projection adjusted.",
        "The model updates in real time.",
        "",
        "#EdgeEquation #WeatherAlert",
    ])[:MAX_CHARS]
