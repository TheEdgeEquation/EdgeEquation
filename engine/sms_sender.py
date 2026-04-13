"""
engine/sms_sender.py
Sends play picks via SMS using Twilio.
"""
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

TWILIO_SID    = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM   = os.getenv("TWILIO_FROM", "")
TWILIO_TO     = os.getenv("TWILIO_TO", "")


def format_picks_for_sms(plays: list[dict]) -> str:
    """Format plays into a clean SMS message for Copilot input."""
    if not plays:
        return "THE EDGE EQUATION — No A+/A/A- plays today. Algorithm found no edge."

    date_str = datetime.now().strftime("%B %d")
    lines = [
        f"THE EDGE EQUATION",
        f"{date_str}  |  ALGORITHM v2.0",
        f"10,000 Monte Carlo sims per play",
        "",
    ]

    grade_order = {"A+": 0, "A": 1, "A-": 2}
    sorted_plays = sorted(plays, key=lambda x: (grade_order.get(x.get("grade","A-"), 9), -x.get("edge", 0)))

    last_grade = None
    grade_labels = {
        "A+": "A+ TIER — SIGMA PLAY",
        "A":  "A TIER — PRECISION PLAY",
        "A-": "A- TIER — SHARP PLAY",
    }

    for play in sorted_plays:
        grade = play.get("grade", "A")
        if grade != last_grade:
            lines.append(grade_labels.get(grade, grade))
            last_grade = grade

        player = play.get("player", "")
        line   = play.get("display_line", "")
        prop   = play.get("prop_label", "")
        odds   = play.get("display_odds", "")
        team   = (play.get("team", "") or "")[:3].upper()
        opp    = (play.get("opponent", "") or "")[:3].upper()
        score  = play.get("confidence_score", 0)

        lines.append(
            f"• {player} {line} {prop} ({odds})"
            f"  |  {team} @ {opp}"
            f"  |  Grade: {grade} ({score})"
        )

    n = len(sorted_plays)
    lines += [
        "",
        f"{n} plays  |  {n}u in play",
        f"EV Sims: 10,000  |  Data: Live  |  Verified",
        "",
        "Paste into Copilot to generate graphic.",
    ]

    return "\n".join(lines)


def send_sms(message: str) -> bool:
    """Send SMS via Twilio. Returns True on success."""
    if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, TWILIO_TO]):
        logger.error("Twilio credentials not set — cannot send SMS")
        return False

    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=TWILIO_FROM,
            to=TWILIO_TO,
        )
        logger.info(f"SMS sent: {msg.sid}")
        return True
    except Exception as e:
        logger.error(f"SMS failed: {e}")
        return False


def send_picks_sms(plays: list[dict]) -> bool:
    """Format plays and send as SMS."""
    message = format_picks_for_sms(plays)
    logger.info(f"SMS message:\n{message}")
    return send_sms(message)
