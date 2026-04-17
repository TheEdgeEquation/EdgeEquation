# core/emailer.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Your Gmail address
GMAIL_USER = "ProfessorEdgeCash@gmail.com"

# New environment variable you will set in GitHub Actions or your server
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

    # Gmail SMTP SSL endpoint
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)


def send_fallback_email(mode: str, text: str, error: str, wal_id: str):
    """
    Sends a fallback email when posting to X fails after all retries.
    """
    subject = f"[EDGE FAILSAFE] {mode} failed to post"

    from core.formatting import (
    format_insight_block,
    format_edges_block,
    format_spotlight_block
)
import json

def send_failsafe_email(mode, wal_id, error, payload):
    body = f"""
    Mode: {mode}
    WAL ID: {wal_id}
    Error: {error}
    ...
    """
    send_email(body)




