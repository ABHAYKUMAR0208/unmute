"""
sms.py — Generic MSG91 SMS sender, shared by taxi bookings and PayU
payment-link notifications.

IMPORTANT — Indian SMS regulation (DLT), not a code limitation:
MSG91 (like every SMS gateway operating in India) will only send SMS
using a pre-approved, DLT-registered template. You cannot send arbitrary
free text. This is why taxi_worker.py's original sender used MSG91's OTP
API with a single numeric code — that's the one type of template that
doesn't need per-message DLT approval.

To actually deliver a real message (e.g. "Your bill is ready, pay here:
<link>") you need MSG91's Flow API instead, with your OWN template
already created + DLT-approved in the MSG91 dashboard, containing
placeholder variables (commonly written as {{VAR1}}, {{VAR2}}, ... in
the MSG91 console). This module calls that API generically — it does
NOT know your template's wording or how many variables it has. You must:

  1. Create + get DLT approval for a template in MSG91's dashboard, e.g.:
     "Dear {{VAR1}}, your Grand Hotel bill of Rs.{{VAR2}} is ready.
      Pay here: {{VAR3}}"
  2. Put that template's ID in MSG91_TEMPLATE_ID_PAYMENT in .env
     (or MSG91_TEMPLATE_ID_FOOD, if you already have a DLT-approved
     food-order template you'd rather reuse for payment notifications)
  3. Call send_sms(phone, {"VAR1": guest_name, "VAR2": amount, "VAR3": link})
     — keys must match your template's variable names exactly.

Until that template exists and is DLT-approved, send_sms() will log a
warning and return False — it will NOT silently fail to notify you.
"""

from __future__ import annotations

import logging
import os

import requests

logger = logging.getLogger("notifications.sms")

MSG91_AUTH_KEY = os.getenv("MSG91_AUTH_KEY", "")
MSG91_FLOW_URL = "https://control.msg91.com/api/v5/flow/"


def _normalize_phone(phone: str) -> str:
    phone = phone.replace("+91", "").replace(" ", "").replace("-", "").strip()
    if phone.startswith("91") and len(phone) == 12:
        phone = phone[2:]
    return phone


def send_sms(phone: str, variables: dict[str, str], template_id: str | None = None) -> bool:
    """
    Send an SMS using MSG91's Flow API with a DLT-approved template.

    template_id defaults to MSG91_TEMPLATE_ID_PAYMENT from the environment
    if not passed explicitly (so callers can share one payment-notification
    template without repeating the env var name everywhere).
    """
    template_id = (
        template_id
        or os.getenv("MSG91_TEMPLATE_ID_PAYMENT", "")
        or os.getenv("MSG91_TEMPLATE_ID_FOOD", "")
    )

    if not MSG91_AUTH_KEY or not template_id:
        logger.warning(
            "MSG91_AUTH_KEY or MSG91_TEMPLATE_ID_PAYMENT not set — skipping SMS "
            "(this requires a DLT-approved template; see module docstring)"
        )
        return False

    if not phone:
        logger.warning("No phone number provided — skipping SMS")
        return False

    mobile = "91" + _normalize_phone(phone)
    payload = {
        "template_id": template_id,
        "short_url": "0",
        "realTimeResponse": "1",
        "recipients": [{"mobiles": mobile, **variables}],
    }
    headers = {"authkey": MSG91_AUTH_KEY, "content-type": "application/json"}

    try:
        r = requests.post(MSG91_FLOW_URL, json=payload, headers=headers, timeout=10)
        data = r.json()
        if r.status_code == 200 and data.get("type") == "success":
            logger.info("SMS sent -> %s via template %s", mobile, template_id)
            return True
        logger.error("MSG91 Flow API error: %s", data)
        return False
    except Exception:
        logger.exception("MSG91 Flow API request failed")
        return False
