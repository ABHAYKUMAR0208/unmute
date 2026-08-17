"""
email.py — Generic SendGrid email sender, shared by taxi bookings and
PayU payment-link notifications.

Unlike SMS, plain transactional email has no DLT-style restriction — any
subject/body is fine. This is a straight generalization of
taxi_worker.py's send_confirmation_email, minus the taxi-specific fields.

Now supports HTML bodies (with an optional plain-text fallback) so callers
can send branded templates instead of raw text.
"""

from __future__ import annotations

import logging
import os

import requests

logger = logging.getLogger("notifications.email")

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "")
SENDGRID_FROM_NAME = os.getenv("HOTEL_NAME", "Grand Hotel")
SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"


def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    body: str,
    html_body: str | None = None,
) -> bool:
    """
    Send a transactional email via SendGrid.

    - If html_body is provided, the email is sent as multipart
      (text/plain fallback + text/html) — recommended for anything
      guest-facing, since plain text is what triggers spam filters and
      looks unpolished.
    - If html_body is omitted, behavior is unchanged from before
      (plain text only) — existing callers keep working with no edits.
    """
    if not SENDGRID_API_KEY:
        logger.warning("SENDGRID_API_KEY not set — skipping email")
        return False
    if not SENDGRID_FROM_EMAIL:
        logger.warning("SENDGRID_FROM_EMAIL not set — skipping email")
        return False
    if not to_email:
        logger.warning("No recipient email provided — skipping email")
        return False

    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json",
    }

    content = [{"type": "text/plain", "value": body}]
    if html_body:
        content.append({"type": "text/html", "value": html_body})

    payload = {
        "personalizations": [{"to": [{"email": to_email, "name": to_name}], "subject": subject}],
        "from": {"email": SENDGRID_FROM_EMAIL, "name": SENDGRID_FROM_NAME},
        "content": content,
    }

    try:
        r = requests.post(SENDGRID_URL, json=payload, headers=headers, timeout=10)
        if r.status_code == 202:
            logger.info("Email sent -> %s", to_email)
            return True
        logger.error("SendGrid error: %s | %s", r.status_code, r.text)
        return False
    except Exception:
        logger.exception("SendGrid request failed")
        return False