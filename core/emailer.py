# core/emailer.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json

from core.formatting import (
    format_insight_block,
    format_edges_block,
    format_spotlight_block
)

# Gmail sender
GMAIL_USER = "ProfessorEdgeCash@gmail.com"
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")


def send_email(subject: str, body: str, to: str = GMAIL_USER):
    """
    Sends a plain-text email using Gmail SMTP + App Password.
    """
    if not GMAIL_PASS:
        raise RuntimeError("GMAIL_APP_PASSWORD environment variable is missing.")

    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = to
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)


# ---------------------------------------------------------
# PREMIUM FAILSAFE EMAIL BODY (STEP 4)
# ---------------------------------------------------------

def build_failsafe_email_body(mode: str, wal_id: str, error: str, payload: dict) -> str:
    """
    Builds the full fallback email body with:
    - Mode
    - WAL ID
    - Error
    - Premium formatted block
    - Pretty JSON payload
    """

    pretty_json = json.dumps(payload, indent=2, default=str)

    # Select correct premium formatter
    if mode == "fact_domestic":
        formatted = format_insight_block("MLB Insight", payload)

    elif mode == "fact_overseas":
        formatted = format_insight_block("KBO/NPB Insight", payload)

    elif mode in ("edges_morning", "edges_evening"):
        formatted = format_edges_block(payload)

    elif mode == "spotlight":
        formatted = format_spotlight_block(payload)

    else:
        formatted = "(No formatter available for this mode)"

    body = f"""
Mode: {mode}
WAL ID: {wal_id}
Error: {error}

--- TEXT THAT WOULD HAVE POSTED ---
{formatted}

--- JSON PAYLOAD ---
{pretty_json}

This was automatically sent because X returned repeated errors.
"""
    return body


# ---------------------------------------------------------
# FAILSAFE EMAIL SENDER
# ---------------------------------------------------------

def send_fallback_email(mode: str, text: str, error: str, wal_id: str, payload: dict = None):
    """
    Sends a fallback email when posting to X fails after all retries.
    """
    subject = f"[EDGE FAILSAFE] {mode} failed to post"

    # If payload wasn't passed, fall back to raw text
    if payload is None:
        body = f"""
Mode: {mode}
WAL ID: {wal_id}
Error: {error}

--- TEXT THAT WOULD HAVE POSTED ---
{text}

This was automatically sent because X returned repeated errors.
"""
    else:
        body = build_failsafe_email_body(mode, wal_id, error, payload)

    send_email(subject, body)
