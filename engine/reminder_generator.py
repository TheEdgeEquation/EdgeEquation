import logging
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
 
def generate_daily_todo(plays, game_parlay=None, pp_parlay=None, has_clv=False, has_weather_alert=False):
    steps = []
    n = len(plays) if plays else 0
    if n > 0:
        steps.append("Step 1 — GRAPHIC (5 min): Copy Section 1 picks → paste into Copilot → generate graphic → post to X")
        steps.append("Step 2 — ANALYSIS (2 min): Copy Section 2 analysis → paste to X as reply or separate post")
    else:
        steps.append("Step 1 — NO PLAY POST: Copy the no-play text below → post to X")
        return "\n".join(["YOUR TO-DO LIST TODAY", "=" * 30, ""] + steps + [""])
    if game_parlay:
        steps.append("Step 3 — PARLAY (1 min): Algorithm approved a parlay — copy Section 3 → post to X")
    if pp_parlay:
        steps.append("Step 4 — PRIZEPICKS (1 min): Algorithm approved a slip — copy Section 4 → post to X")
    if has_clv:
        steps.append("BONUS — CLV ALERT: Line moved our way — copy CLV post below → post to X now for credibility")
    if has_weather_alert:
        steps.append("WEATHER ALERT: Conditions changed — copy weather post below → post to X")
    est_time = "~" + str(len(steps) * 2 + 3) + " min total"
    lines = [
        "YOUR TO-DO LIST TODAY (" + est_time + ")",
        "=" * 40,
        "",
    ]
    lines.extend(steps)
    lines.append("")
    lines.append("Everything else fires automatically.")
    lines.append("")
    return "\n".join(lines)
 
 
def generate_weekly_todo(stats, week_num=1):
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    win_rate = stats.get("win_rate", 0)
    net_units = stats.get("net_units", 0)
    prefix = "+" if net_units >= 0 else ""
    lines = [
        "YOUR WEEKLY TO-DO LIST — Week " + str(week_num),
        "=" * 40,
        "",
        "Week " + str(week_num) + " record: " + str(wins) + "-" + str(losses) + " (" + str(win_rate) + "%) " + prefix + str(net_units) + "u",
        "",
        "Step 1 — ACCOUNTABILITY THREAD (5 min): Copy Section A below → post as thread to X",
        "Step 2 — WEEKLY POLL (1 min): Copy Section B → post to X",
        "Step 3 — MODEL vs VEGAS (2 min): Copy Section C → post to X",
        "",
        "Sunday weekly roundup auto-posted already.",
        "",
        "Total time: ~8 minutes",
        "",
    ]
    return "\n".join(lines)
 
 
def generate_monthly_todo(stats, month_num=1):
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    win_rate = stats.get("win_rate", 0)
    roi = stats.get("roi", 0)
    prefix = "+" if roi >= 0 else ""
    lines = [
        "YOUR MONTHLY TO-DO LIST — Month " + str(month_num),
        "=" * 40,
        "",
        "Month " + str(month_num) + " record: " + str(wins) + "-" + str(losses) + " (" + str(win_rate) + "%) ROI: " + prefix + str(roi) + "%",
        "",
        "Step 1 — CALIBRATION THREAD (5 min): Copy Section A → post as thread to X",
        "Step 2 — ORIGIN STORY check: Is it pinned? If not pin it now.",
        "",
        "Total time: ~5 minutes",
        "",
    ]
    return "\n".join(lines)
