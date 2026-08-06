"""
billing_service.py — Creates a PayU bill directly from CRM-extracted data
(crm/extractor.py's output), instead of PaymentBridge's live in-call
transcript regex extraction.

Called from crm/worker.py right after a successful HubSpot push, reusing
the exact same LLM-extracted `items` (name+quantity) — no re-extraction,
no regex, no live-call timing dependency, so quantities always match what
CRM shows.

Trade-off (accepted, by design): the guest gets the payment link a few
seconds after the call ends — once the transcript's quiet-period timer
fires and the LLM extraction finishes — rather than instantly mid-call.
This module intentionally does NOT try to run during the live call.

Only service types with a real items+quantity shape in extractor.py's
current schema are billed this way: food_order, laundry. "taxi" and
"maintenance" don't carry billable items in the current extraction
schema (see SYSTEM_PROMPT in extractor.py) and are skipped — logged, not
billed, not guessed at with fabricated fields.
"""

from __future__ import annotations

import logging
from typing import Optional

from .bill_generator import BillGenerator
from .config import PayuWorkerSettings
from .models import BillItem, ServiceRequest, ServiceType
from .payu_client import PayUClient
from .service_catalog import lookup_price
from ..notifications.email import send_email
from ..notifications.sms import send_sms, send_payment_ready_otp_style
from ..taxi.hubspot_client import fetch_guest as fetch_guest_from_hubspot

logger = logging.getLogger("payments.billing_service")

_CRM_TO_PAYMENTS_SERVICE_TYPE = {
    "food_order": ServiceType.FOOD_ORDER,
    "laundry": ServiceType.LAUNDRY,
}

# Lazily-built singletons — same pattern PaymentBridge used, just moved
# here since this module now owns bill creation.
_settings: Optional[PayuWorkerSettings] = None
_bill_gen: Optional[BillGenerator] = None
_payu_client: Optional[PayUClient] = None


def _get_settings() -> PayuWorkerSettings:
    global _settings
    if _settings is None:
        _settings = PayuWorkerSettings()
    return _settings


def _get_bill_generator() -> BillGenerator:
    global _bill_gen
    if _bill_gen is None:
        _bill_gen = BillGenerator(_get_settings())
    return _bill_gen


def _get_payu_client() -> PayUClient:
    global _payu_client
    if _payu_client is None:
        _payu_client = PayUClient(_get_settings())
    return _payu_client


def create_bill_from_crm_data(data: dict) -> Optional[dict]:
    """
    `data` is exactly what crm/extractor.py produced (the same dict
    already pushed to HubSpot) — e.g.:
        {"service_type": "food_order", "room_number": "999",
         "items": [{"name": "burger", "quantity": 10}], "special_notes": ..., ...}

    Returns {"order_id", "payment_link", "bill_text", "total"} on success,
    or None if this record isn't billable (wrong service_type, no room
    number, no items, or no catalog price match). Never raises — a
    billing failure must never break the CRM pipeline that calls this.
    """
    service_type_str = data.get("service_type", "")
    payments_service_type = _CRM_TO_PAYMENTS_SERVICE_TYPE.get(service_type_str)
    if payments_service_type is None:
        logger.info(
            "Skipping billing for service_type=%r — not a billable-items type "
            "in the current extraction schema (see _CRM_TO_PAYMENTS_SERVICE_TYPE)",
            service_type_str,
        )
        return None

    room_number = data.get("room_number")
    if not room_number or str(room_number).lower() in ("null", "none", ""):
        logger.warning("Skipping billing — no valid room_number in CRM data: %r", room_number)
        return None
    room_number = str(room_number)

    raw_items = data.get("items") or []
    if not raw_items:
        logger.warning("Skipping billing for room %s — no items in CRM data", room_number)
        return None

    bill_items: list[BillItem] = []
    for it in raw_items:
        name = str(it.get("name", "")).strip()
        if not name:
            continue
        try:
            qty = int(it.get("quantity") or 1)
        except (TypeError, ValueError):
            qty = 1
        price = lookup_price(payments_service_type, name)
        if price is None:
            logger.warning(
                "No catalog price for item %r (service=%s) — skipping this item, "
                "not billing a guessed price", name, service_type_str,
            )
            continue
        bill_items.append(BillItem(name=name, quantity=qty, unit_price=price))

    if not bill_items:
        logger.warning("Skipping billing for room %s — no priceable items after catalog lookup", room_number)
        return None

    # Guest contact — same HubSpot-by-room lookup used before, just called
    # from here now instead of payment_bridge.py.
    guest_name, guest_phone, guest_email = "Guest", "9999999999", "guest@hotel.com"
    try:
        result = fetch_guest_from_hubspot(room_number=room_number)
        if result.found:
            guest_name = result.guest_name or guest_name
            guest_email = result.guest_email or guest_email
            guest_phone = result.guest_phone or guest_phone
            logger.info(
                "HubSpot guest match for room %s: name=%s email=%s phone=%s",
                room_number, guest_name, guest_email, guest_phone,
            )
        else:
            logger.info("No HubSpot guest record for room %s — using placeholder contact info", room_number)
    except Exception:
        logger.exception("HubSpot guest lookup failed for room %s", room_number)

    try:
        request = ServiceRequest(
            service_type=payments_service_type,
            room_number=room_number,
            guest_name=guest_name,
            guest_phone=guest_phone,
            guest_email=guest_email,
            items=bill_items,
            notes=str(data.get("special_notes") or "")[:200],
        )
        bill_gen = _get_bill_generator()
        bill, _created = bill_gen.create_bill(request)

        payu = _get_payu_client()
        payu.create_payment(bill)
        payment_link = payu.get_payment_page_url(bill)
        bill_gen.update_payment_link(bill.order_id, payment_link)
        bill_text = bill_gen.format_bill_text(bill)

        logger.info(
            "Bill ready (from CRM data) — order=%s total=Rs%.2f link=%s",
            bill.order_id, bill.total, payment_link,
        )
    except Exception:
        logger.exception("Failed to create bill from CRM data for room %s", room_number)
        return None

    # Notify guest — same pattern payment_bridge.py used: try the real
    # link-carrying SMS first, fall back to the OTP-style code-only SMS.
    sms_ok = send_sms(guest_phone, {
        "VAR1": guest_name, "VAR2": f"{bill.total:.2f}", "VAR3": payment_link,
    })
    if not sms_ok:
        otp_ok = send_payment_ready_otp_style(guest_phone, bill.order_id)
        if not otp_ok:
            logger.info("Neither Flow-API SMS nor OTP-style fallback sent for order %s", bill.order_id)

    email_ok = send_email(
        to_email=guest_email,
        to_name=guest_name,
        subject="Your bill is ready — pay online",
        body=(
            f"Dear {guest_name},\n\n{bill_text}\n\n"
            f"Pay securely here: {payment_link}\n\nThank you!"
        ),
    )
    if not email_ok:
        logger.info("Payment-link email not sent for order %s", bill.order_id)

    return {
        "order_id": bill.order_id,
        "payment_link": payment_link,
        "bill_text": bill_text,
        "total": bill.total,
    }