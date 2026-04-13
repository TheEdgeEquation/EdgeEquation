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
    lines += ["", str(n) + " plays  |  " + str(n) + "u in play", "EV Sims: 10,000  |  Data: Live  |  Verified", "", "Paste into Copilot to generate graphic."]
    return "\n".join(lines)
 
 
def format_analysis_section(analyses):
    if not analyses:
        return "No analysis available."
    lines = []
    for i, item in enumerate(analyses):
        if i > 0:
            lines.append("-" * 40)
        lines.append(item.get("text", ""))
        lines.append("")
    return "\n".join(lines)
 
 
def format_parlay_section(parlay):
    if not parlay:
        return "No edge game parlay today. Algorithm did not clear the 10% threshold."
    legs = parlay.get("legs", [])
    edge = parlay.get("edge", 0)
    grade = parlay.get("grade", "A-")
    score = parlay.get("confidence_score", 88)
    n = parlay.get("leg_count", 0)
    lines = ["ALGORITHM PARLAY — " + str(n) + " LEGS", "Grade: " + grade + " (" + str(score) + ")  |  Combined Edge: +" + str(round(edge*100, 1)) + "%", "ML + SPREADS + TOTALS ONLY", ""]
    for i, leg in enumerate(legs):
        lines.append(str(i+1) + ". " + leg.get("pick", "") + " (" + str(leg.get("display_odds", "")) + ")")
        lines.append("   " + leg.get("game", "") + "  |  Edge: +" + str(round(leg.get("edge", 0)*100, 1)) + "%")
        lines.append("")
    lines += ["Only posts when the math says yes.", "10,000 sims. Live data. No feelings. Just facts."]
    return "\n".join(lines)
 
 
def format_prizepicks_section(slip):
    if not slip:
        return "No edge PrizePicks slip today. Not enough props cleared the threshold."
    legs = slip.get("legs", [])
    edge = slip.get("edge", 0)
    grade = slip.get("grade", "A-")
    n = slip.get("leg_count", 0)
    lines = ["PRIZEPICKS SLIP — " + str(n) + " LEGS", "Grade: " + grade + "  |  Combined Edge: +" + str(round(edge*100, 1)) + "%", ""]
    for i, leg in enumerate(legs):
        player = leg.get("player", "")
        dl = leg.get("display_line", "")
        prop = leg.get("prop_label", "")
        odds = leg.get("display_odds", "")
        sport = leg.get("sport_label", "")
        edge_pct = str(round(leg.get("edge", 0)*100, 1))
        lines.append(str(i+1) + ". " + player + " " + dl + " " + prop + " (" + odds + ")")
        lines.append("   " + sport + "  |  Edge: +" + edge_pct + "%")
        lines.append("")
    lines += ["Algorithm approved. Only posts when the equation says yes."]
    return "\n".join(lines)
 
 
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
    by_sport = all_time_stats.get("by_sport", {})
    avg_clv = all_time_stats.get("avg_clv", 0)
    prefix = "+" if profit >= 0 else ""
    lines = [
        "BANKROLL UPDATE",
        "Starting: $1,000 (100u)  |  Current: $" + str(round(current*10, 2)) + " (" + str(current) + "u)",
        "P/L: " + prefix + str(profit) + "u ($" + str(round(profit*10, 2)) + ")  |  ROI: " + prefix + str(roi) + "%",
        "Record: " + str(wins) + "-" + str(losses) + " (" + str(win_rate) + "%)",
        "",
        "By grade:",
    ]
    for grade in ("A+", "A", "A-"):
        g = by_grade.get(grade, {})
        if g.get("total", 0) > 0:
            lines.append("  " + grade + ": " + str(g["wins"]) + "-" + str(g["total"]-g["wins"]) + " (" + str(g["win_rate"]) + "%)")
    lines.append("")
    lines.append("By sport:")
    for sport, data in by_sport.items():
        if data.get("total", 0) > 0:
            lines.append("  " + sport + ": " + str(data["wins"]) + "-" + str(data["total"]-data["wins"]) + " (" + str(data["win_rate"]) + "%)")
    if avg_clv != 0:
        lines += ["", "Avg closing line value: +" + str(avg_clv) + "%"]
    return "\n".join(lines)
 
 
def send_daily_email(plays, analyses, game_parlay, pp_parlay, personal_parlay, personal_pp, bankroll_summary, all_time_stats, todo_text, clv_post=None, why_passed=None):
    n = len(plays) if plays else 0
    has_parlay = " + Parlay" if game_parlay else ""
    has_slip = " + Slip" if pp_parlay else ""
    subject = "EDGE EQUATION — " + datetime.now().strftime("%B %d") + " | " + str(n) + " Plays" + has_parlay + has_slip
    sep = "=" * 50
    sections = [
        todo_text,
        sep, "SECTION 1 — PICKS (paste into Copilot for graphic)", sep,
        format_picks_section(plays),
        "", sep, "SECTION 2 — ANALYSIS (paste to X)", sep,
        format_analysis_section(analyses),
        "", sep, "SECTION 3 — ALGORITHM PARLAY (post to X if approved)", sep,
        format_parlay_section(game_parlay),
        "", sep, "SECTION 4 — PRIZEPICKS SLIP (post to X if approved)", sep,
        format_prizepicks_section(pp_parlay),
    ]
    if why_passed:
        sections += ["", sep, "BONUS — WHY WE PASSED (post to X for engagement)", sep, why_passed]
    if clv_post:
        sections += ["", sep, "CLV ALERT — POST THIS NOW", sep, clv_post]
    from engine.kelly_calculator import calculate_parlay_units
    personal_units = calculate_parlay_units(personal_parlay.get("legs", [])) if personal_parlay else 0.5
    sections += [
        "", sep, "SECTION 5 — YOUR BEST PARLAY (personal, not posted)", sep,
        format_personal_parlay_section(personal_parlay, personal_units),
        "", sep, "SECTION 6 — YOUR BEST PRIZEPICKS SLIP (personal, not posted)", sep,
        format_personal_pp_section(personal_pp, 0.5),
        "", sep, "SECTION 7 — BANKROLL UPDATE", sep,
        format_bankroll_section(bankroll_summary, all_time_stats),
    ]
    body = "\n".join(sections)
    return _send(subject, body)
 
 
def send_no_play_email():
    from engine.content_generator import generate_no_play_post
    subject = "EDGE EQUATION — " + datetime.now().strftime("%B %d") + " | No Plays Today"
    no_play = generate_no_play_post()
    body = "\n".join([
        "NO PLAYS TODAY",
        "=" * 40,
        "",
        "The algorithm found no edge today.",
        "",
        "POST THIS TO X:",
        "",
        no_play,
    ])
    return _send(subject, body)
 
 
def send_results_email(results):
    from engine.content_generator import generate_results_post
    subject = "EDGE EQUATION — " + datetime.now().strftime("%B %d") + " RESULTS"
    body = generate_results_post(results)
    return _send(subject, body)
