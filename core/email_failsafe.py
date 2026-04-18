# core/email_failsafe.py
"""
Failsafe email sender for The Edge Equation.

Used when:
- X posting fails after all retries
- You still want the content in your hands
"""

import os
import smtplib
from email.message import EmailMessage
from typing import Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SMTP_HOST = os.getenv("FAILSAFE_SMTP_HOST", "smtp.yourprovider.com")
SMTP_PORT = int(os.getenv("FAILSAFE_SMTP_PORT", "587"))
SMTP_USER = os.getenv("FAILSAFE_SMTP_USER", "your-user@example.com")
SMTP_PASS = os.getenv("FAILSAFE_SMTP_PASS", "your-password")

FAILSAFE_FROM = os.getenv("FAILSAFE_FROM", "edge-failsafe@example.com")
FAILSAFE_TO = os.getenv("FAILSAFE_TO", "you@example.com")


# ---------------------------------------------------------------------------
# Core Failsafe Function
# ---------------------------------------------------------------------------

def send_failsafe_email(
    subject: str,
    body: str,
    attachment_path: Optional[str] = None,
) -> None:
    """
    Send a failsafe email with optional attachment.

    This must NEVER raise in a way that breaks the caller.
    """

    try:
        msg = EmailMessage()
        msg["From"] = FAILSAFE_FROM
        msg["To"] = FAILSAFE_TO
        msg["Subject"] = subject
        msg.set_content(body)

        if attachment_path:
            try:
                with open(attachment_path, "rb") as f:
                    data = f.read()
                filename = attachment_path.split("/")[-1]
                msg.add_attachment(
                    data,
                    maintype="application",
                    subtype="octet-stream",
                    filename=filename,
                )
            except Exception:
                # Attachment failure should not block the email itself
                pass

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            if SMTP_USER and SMTP_PASS:
                server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

    except Exception:
        # Failsafe must never crash the main flow
        pass
