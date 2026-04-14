import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_SMTP = os.getenv("EMAIL_SMTP", "smtp.gmail.com")
EMAIL_PORT = 587
 
 
def _send(subject, body):
    if not all([EMAIL_FROM, EMAIL_TO, EMAIL_PASSWORD]):
        logger.error("Email credentials not set")
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(EMAIL_SMTP, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        logger.info("Email sent: " + subject)
        return True
    except Exception as e:
        logger.error("Email failed: " + str(e))
        return False
 
 
def format_picks_section(plays):
    if not plays:
        return "No A+/A/A- plays today. Algorithm found no edge."
    date_str = datetime.now().strftime("%B %d")
    lines = ["THE EDGE EQUATION", date_str + "  |  ALGORITHM v2.0", "10,000 Monte Carlo sims per play", ""]
    grade_order = {"A+": 0, "A": 1, "A-": 2}
    sorted_plays = sorted(plays, key=lambda x: (grade_order.get(x.get("grade", "A-"), 9), -x.get("edge", 0)))
    last_grade = None
    grade_labels = {"A+": "A+ TIER — SIGMA PLAY", "A": "A TIER — PRECISION PLAY", "A-": "A- TIER — SHARP PLAY"}
    for play in sorted_plays:
        grade = play.get("grade", "A")
        if grade != last_grade:
            lines.append(grade_labels.get(grade, grade))
            last_grade = grade
        player = play.get("player", "")
        dl = play.get("display_line", "")
        prop = play.get("prop_label", "")
        odds = play.get("display_odds", "")
        team = (play.get("team", "") or "")[:3].upper()
        opp = (play.get("opponent", "") or "")[:3].upper()
        score = play.get("confidence_score", 0)
        units = play.get("recommended_units", 0.5)
        lines.append("* " + player + " " + dl + " " + prop + " (" + odds + ")  |  " + team + " @ " + opp + "  |  Grade: " + grade + " (" + str(score) + ")  |  " + str(units) + "u")
    n = len(sorted_plays)
    lines += ["", str(n) + " plays  |  EV Sims: 10,000  |  Data: Live  |  Verified"]
    return "\n".join(lines)
 
 
def format_projection_sections(mlb_games, mlb_pitchers, nba_games, nhl_games, nrfi_plays):
    from engine.content_generator import (
        generate_mlb_projection_post,
        generate_pitcher_projection_post,
        generate_nba_projection_post,
        generate_nhl_projection_post,
        generate_nrfi_probability_post,
    )
    sep = "=" * 50
    sections = []
    if mlb_games:
        sections.append(sep)
        sections.append("MLB GAME PROJECTIONS (copy/paste to X):")
        sections.append(sep)
        sections.append(generate_mlb_projection_post(mlb_games))
    if mlb_pitchers:
        sections.append("")
        sections.append(sep)
        sections.append("MLB PITCHER PROJECTIONS (copy/paste to X):")
        sections.append(sep)
        sections.append(generate_pitcher_projection_post(mlb_pitchers))
    if nba_games:
        sections.append("")
        sections.append(sep)
        sections.append("NBA PROJECTIONS (copy/paste to X):")
        sections.append(sep)
        sections.append(generate_nba_projection_post(nba_games))
    if nhl_games:
        sections.append("")
        sections.append(sep)
        sections.append("NHL PROJECTIONS (copy/paste to X):")
        sections.append(sep)
        sections.append(generate_nhl_projection_post(nhl_games))
    if nrfi_plays:
        sections.append("")
        sections.append(sep)
        sections.append("NRFI/YRFI PROBABILITIES (copy/paste to X):")
        sections.append(sep)
        sections.append(generate_nrfi_probability_post(nrfi_plays))
    return "\n".join(sections)
 
 
def format_personal_parlay_section(parlay, kelly_units=0.5):
    from engine.personal_engine import format_personal_parlay_text
    return format_personal_parlay_text(parlay, kelly_units)
 
 
def format_personal_pp_section(slip, kelly_units=0.5):
    from engine.personal_engine import format_personal_prizepicks_text
    return format_personal_prizepicks_text(slip, kelly_units)
 
 
def format_bankroll_section(bankroll_summary, all_time_stats):
    current = bankroll_summary.get("current_units", 100.0)
    profit = bankroll_summary.get("profit_units", 0)
    roi = bankroll_summary.get("roi_pct", 0)
    wins = all_time_stats.get("wins", 0)
    losses = all_time_stats.get("losses", 0)
    win_rate = all_time_stats.get("win_rate", 0)
    by_grade = all_time_stats.get("by_grade", {})
    avg_clv = all_time_stats.get("avg_clv", 0)
    prefix = "+" if profit >= 0 else ""
    lines = [
        "BANKROLL UPDATE",
        "Starting: $1,000 (100u)  |  Current: $" + str(round(current*10, 2)) + " (" + str(current) + "u)",
        "P/L: " + prefix + str(profit) + "u  |  ROI: " + prefix + str(roi) + "%",
        "Record: " + str(wins) + "-" + str(losses) + " (" + str(win_rate) + "%)",
        "",
        "By grade:",
    ]
    for grade in ("A+", "A", "A-"):
        g = by_grade.get(grade, {})
        if g.get("total", 0) > 0:
            lines.append("  " + grade + ": " + str(g["wins"]) + "-" + str(g["total"]-g["wins"]) + " (" + str(g["win_rate"]) + "%)")
    if avg_clv != 0:
        lines += ["", "Avg closing line value: +" + str(avg_clv) + "%"]
    return "\n".join(lines)
 
 
def send_daily_email(plays, analyses, game_parlay, pp_parlay, personal_parlay, personal_pp, bankroll_summary, all_time_stats, todo_text, mlb_games=None, mlb_pitchers=None, nba_games=None, nhl_games=None, nrfi_plays=None, clv_post=None, why_passed=None):
    n = len(plays) if plays else 0
    date_str = datetime.now().strftime("%B %d")
    subject = "EDGE EQUATION — " + date_str + " | Projections + " + str(n) + " Personal Plays"
    sep = "=" * 50
    body_parts = [todo_text]
    body_parts += [
        sep,
        "SECTION 1 — PUBLIC PROJECTIONS (copy/paste to X)",
        sep,
        format_projection_sections(mlb_games or [], mlb_pitchers or [], nba_games or [], nhl_games or [], nrfi_plays or []),
    ]
    if plays:
        body_parts += [
            "",
            sep,
            "SECTION 2 — YOUR PERSONAL PICKS (not posted publicly)",
            sep,
            format_picks_section(plays),
        ]
    if analyses:
        from engine.analysis_generator import generate_all_analysis
        body_parts += [
            "",
            sep,
            "SECTION 3 — ANALYSIS TEXT (copy/paste to X after graphic)",
            sep,
        ]
        for item in analyses:
            body_parts.append(item.get("text", ""))
            body_parts.append("-" * 40)
    if game_parlay:
        from engine.parlay_engine import format_game_parlay_sms
        body_parts += [
            "",
            sep,
            "SECTION 4 — ALGORITHM PARLAY (post to X if approved)",
            sep,
            format_game_parlay_sms(game_parlay) or "No edge parlay today.",
        ]
    if pp_parlay:
        from engine.parlay_engine import format_prizepicks_sms
        body_parts += [
            "",
            sep,
            "SECTION 5 — PRIZEPICKS SLIP (post to X if approved)",
            sep,
            format_prizepicks_sms(pp_parlay) or "No edge slip today.",
        ]
    if clv_post:
        body_parts += ["", sep, "CLV ALERT — POST THIS NOW", sep, clv_post]
    from engine.kelly_calculator import calculate_parlay_units
    personal_units = calculate_parlay_units(personal_parlay.get("legs", [])) if personal_parlay else 0.5
    body_parts += [
        "",
        sep,
        "SECTION 6 — YOUR BEST PERSONAL PARLAY (not posted)",
        sep,
        format_personal_parlay_section(personal_parlay, personal_units),
        "",
        sep,
        "SECTION 7 — YOUR BEST PRIZEPICKS SLIP (not posted)",
        sep,
        format_personal_pp_section(personal_pp, 0.5),
        "",
        sep,
        "SECTION 8 — BANKROLL UPDATE",
        sep,
        format_bankroll_section(bankroll_summary, all_time_stats),
    ]
    body = "\n".join(body_parts)
    return _send(subject, body)
 
 
def send_no_play_email():
    from engine.content_generator import generate_no_play_post
    subject = "EDGE EQUATION — " + datetime.now().strftime("%B %d") + " | No Plays Today"
    no_play = generate_no_play_post()
    body = "\n".join(["NO PLAYS TODAY", "=" * 40, "", "POST THIS TO X:", "", no_play])
    return _send(subject, body)
 
 
def send_results_email(results):
    from engine.content_generator import generate_results_post
    subject = "EDGE EQUATION — " + datetime.now().strftime("%B %d") + " RESULTS"
    body = generate_results_post(results)
    return _send(subject, body)
 
 
def send_projections_only_email(mlb_games, mlb_pitchers, nba_games, nhl_games, nrfi_plays, personal_parlay=None, personal_pp=None, bankroll_summary=None, all_time_stats=None):
    from engine.content_generator import get_daily_cta
    date_str = datetime.now().strftime("%B %d")
    subject = "EDGE EQUATION — " + date_str + " | Daily Projections"
    sep = "=" * 50
    todo = "\n".join([
        "YOUR TO-DO LIST TODAY (~5 min)",
        "=" * 40,
        "",
        "Step 1 — MLB POST (2 min): Copy MLB section → paste to X",
        "Step 2 — PITCHER POST (1 min): Copy pitcher section → paste to X",
        "Step 3 — NBA/NHL POST (1 min): Copy relevant section → paste to X",
        "Step 4 — NRFI POST (1 min): Copy NRFI section → paste to X",
        "",
        "Everything else fires automatically.",
        "",
    ])
    body_parts = [
        todo,
        format_projection_sections(mlb_games, mlb_pitchers, nba_games, nhl_games, nrfi_plays),
    ]
    if personal_parlay or personal_pp:
        body_parts += ["", sep, "YOUR PERSONAL PLAYS (not posted)", sep]
        if personal_parlay:
            from engine.personal_engine import format_personal_parlay_text
            from engine.kelly_calculator import calculate_parlay_units
            units = calculate_parlay_units(personal_parlay.get("legs", []))
            body_parts.append(format_personal_parlay_text(personal_parlay, units))
        if personal_pp:
            from engine.personal_engine import format_personal_prizepicks_text
            body_parts.append(format_personal_prizepicks_text(personal_pp, 0.5))
    if bankroll_summary and all_time_stats:
        body_parts += ["", sep, "BANKROLL UPDATE", sep, format_bankroll_section(bankroll_summary, all_time_stats)]
    body = "\n".join(body_parts)
    return _send(subject, body)
