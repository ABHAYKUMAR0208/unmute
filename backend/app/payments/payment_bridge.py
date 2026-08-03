"""
payment_bridge.py — Wires the voice agent's live transcript directly to the
PayU billing worker that already exists in this package.

Adapted from an external draft that assumed a different project layout
(`src/payment/`, a `PayUWorker` class, a no-arg `BillGenerator()`). This
version uses the real names in this codebase:

    BillGenerator(settings)          -> app/payments/bill_generator.py
    PayUClient(settings)             -> app/payments/payu_client.py  (not PayUWorker)
    create_bill(request) -> (Bill, created)   (tuple, not a bare Bill)
    get_catalog / lookup_price       -> app/payments/service_catalog.py

Flow:
    Guest speaks
        -> agent.py's on_user_delta/on_assistant_delta call notify_turn()
            -> state machine decides the order is "closed"
                -> items priced from service_catalog.get_catalog()
                    -> BillGenerator.create_bill()   (GST calculated, saved to sqlite)
                        -> PayUClient.create_payment() + get_payment_page_url()
                            -> on_payment_ready(payment_link, bill_text, room_number)
                                -> PayUClient.check_payment_status() polls PayU
                                    -> on_payment_confirmed(...)

Known simplification vs. the original draft: there is no HubSpot
guest-lookup module or separate FoodWorker/MSG91/SendGrid layer in this
project, so guest name/phone/email are taken from the transcript (or
sensible defaults) and every service type — including food — goes
through the same create_bill -> PayU link path already used by
payments/router.py.

CRM push + SMS/email are now wired in below:
    - _push_order_to_crm() pushes the priced order to HubSpot right after
      the bill is created (crm.hubspot_client.push). Only service types
      HubSpot has an object type for (food_order, laundry, and cab_booking
      mapped to HubSpot's "taxi") are pushed; others are logged and
      skipped rather than pushed with fabricated fields.
    - notifications.sms.send_sms / notifications.email.send_email send the
      payment link to the guest's phone/email, not just the browser data
      channel.
    - _sync_payment_to_crm() pushes a "payment" HubSpot record once the
      bill's status resolves (see _poll_for_confirmation).
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Callable, Optional

from .bill_generator import BillGenerator
from .config import PayuWorkerSettings
from .models import BillItem, PaymentStatus, ServiceRequest, ServiceType
from .payu_client import PayUClient
from .service_catalog import get_catalog
from ..crm.hubspot_client import push as crm_push, HubSpotConfigError
from ..notifications.email import send_email
from ..notifications.sms import send_sms

logger = logging.getLogger("payments.bridge")

LOCAL_STATUS_POLL_SECS = 3.0  # cheap local SQLite read, not a call to PayU

# ── Service type keyword detection ───────────────────────────────────────────
_SERVICE_KEYWORDS: dict[str, list[str]] = {
    "food_order": [
        "food", "eat", "order", "hungry", "meal", "dinner", "lunch",
        "breakfast", "menu", "dish", "snack", "chicken", "naan", "biryani",
        "pizza", "burger", "coffee", "tea", "juice", "beer", "coke", "pepsi",
        "butter", "paneer", "dal", "rice", "roti", "manchurian",
    ],
    "room_cleaning": [
        "clean", "housekeeping", "tidy", "maid", "towel", "sweep",
        "vacuum", "bed", "linen", "minibar", "pillow", "blanket",
    ],
    "cab_booking": [
        "cab", "taxi", "ride", "airport", "pickup", "drop", "car",
        "transport", "station", "railway",
    ],
    "laundry": [
        "laundry", "wash", "iron", "press", "dry clean", "clothes",
        "shirt", "trouser", "suit",
    ],
    "spa": [
        "spa", "massage", "facial", "manicure", "pedicure", "relax",
        "therapy", "beauty",
    ],
    "restaurant_booking": [
        "restaurant", "reserve", "table", "booking", "dining",
        "birthday", "anniversary", "cake",
    ],
}

_NUMWORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "a": 1, "an": 1,
}

_AGENT_ECHO_PHRASES = [
    "got it", "alright", "noted", "sure", "of course", "certainly",
    "i have", "i've noted", "i'll add", "added",
]
_AGENT_FINAL_SUMMARY_PHRASES = [
    "to confirm", "just to confirm", "let me confirm", "your order is",
    "order will be", "order will arrive", "order will be ready",
    "your order will", "thank you", "have a wonderful", "goodbye",
    "have a great", "is there anything else i can help",
    "is there anything else", "order has been placed", "order is confirmed",
]
_USER_DONE_PHRASES = [
    "no", "nope", "that's all", "that's it", "that's enough",
    "nothing else", "no more", "no thank", "i'm good", "im good",
    "that will be all", "that would be all", "no that's",
    "thank you", "thanks",
]


def _detect_service_type(text: str) -> Optional[ServiceType]:
    lower = text.lower()
    scores = {svc: sum(1 for kw in kws if kw in lower) for svc, kws in _SERVICE_KEYWORDS.items()}
    best, count = max(scores.items(), key=lambda x: x[1])
    if count == 0:
        return None
    try:
        return ServiceType(best)
    except ValueError:
        return None


def _extract_items(text: str, service_type: ServiceType) -> list[BillItem]:
    """Scan transcript for catalog item names using the real service_catalog.py."""
    catalog = get_catalog(service_type)
    lower = text.lower()
    found, seen = [], set()

    # Longest names first so "gobi manchurian" wins over a bare "rice"/"manchurian"
    for item_name in sorted(catalog, key=len, reverse=True):
        if item_name in seen or item_name not in lower:
            continue
        price = catalog[item_name]
        pattern = r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten|a|an)\s+" + re.escape(item_name)
        m = re.search(pattern, lower)
        if m:
            qty = int(m.group(1)) if m.group(1).isdigit() else _NUMWORDS.get(m.group(1), 1)
        else:
            qty = 1
        found.append(BillItem(name=item_name, quantity=qty, unit_price=price))
        seen.add(item_name)
        lower = lower.replace(item_name, "", 1)  # don't let "rice" re-match inside "lemon rice"
    return found


def _extract_room_number(text: str) -> str:
    for pattern in (
        r"room\s*(?:number\s*)?(\d{2,4})",
        r"room\s+is\s+(\d{2,4})",
        r"(?:i(?:'m| am) in|in room)\s+(\d{2,4})",
        r"(?:it(?:'s| is)|number)\s+(\d{2,4})",
        r"\b(\d{3,4})\b",
    ):
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return ""


def _extract_guest_info(turns: list[tuple[str, str]]) -> dict:
    user_text = " ".join(t for sp, t in turns if sp == "user")
    info = {"guest_name": "Guest", "guest_phone": "9999999999", "guest_email": "guest@hotel.com"}
    name_m = re.search(
        r"(?:my name is|i am|this is|i'm)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        user_text, re.IGNORECASE,
    )
    if name_m:
        info["guest_name"] = name_m.group(1).strip().title()
    phone_m = re.search(r"\b([6-9]\d{9})\b", user_text)
    if phone_m:
        info["guest_phone"] = phone_m.group(1)
    email_m = re.search(r"\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b", user_text, re.IGNORECASE)
    if email_m:
        info["guest_email"] = email_m.group(0)
    return info


class PaymentBridge:
    """
    Listens to transcript turns (call notify_turn() from agent.py's
    on_assistant_delta / on_user_delta) and triggers real bill creation +
    a PayU payment link once an order looks closed.
    """

    def __init__(
        self,
        settings: Optional[PayuWorkerSettings] = None,
        on_payment_ready: Optional[Callable[[str, str, str], None]] = None,
        on_payment_confirmed: Optional[Callable[[str, str, str], None]] = None,
        room_number: str = "",
    ):
        self._settings = settings or PayuWorkerSettings()
        self._on_payment_ready = on_payment_ready
        self._on_payment_confirmed = on_payment_confirmed
        self._room_number = room_number

        self._turns: list[tuple[str, str]] = []
        self._created_keys: set[str] = set()
        self._creating_keys: set[str] = set()
        self._poll_tasks: dict[str, asyncio.Task] = {}
        self._bill_lock = asyncio.Lock()
        self._min_turns = 5

        self._bill_generator: Optional[BillGenerator] = None
        self._payu_client: Optional[PayUClient] = None

    def _get_bill_generator(self) -> BillGenerator:
        if self._bill_generator is None:
            self._bill_generator = BillGenerator(self._settings)
        return self._bill_generator

    def _get_payu_client(self) -> PayUClient:
        if self._payu_client is None:
            self._payu_client = PayUClient(self._settings)
        return self._payu_client

    def set_room_number(self, room_number: str) -> None:
        self._room_number = room_number

    def stop(self) -> None:
        for task in self._poll_tasks.values():
            task.cancel()
        self._poll_tasks.clear()

    def notify_turn(self, speaker: str, text: str) -> None:
        """Call after every transcript turn. speaker = 'user' or 'agent'."""
        self._turns.append((speaker, text))

        if speaker == "user" and not self._room_number:
            extracted = _extract_room_number(text)
            if extracted:
                self._room_number = extracted
                logger.info("Room number detected: %s", extracted)

        if speaker == "agent" and len(self._turns) >= self._min_turns:
            asyncio.ensure_future(self._maybe_create_bill())

    async def _maybe_create_bill(self) -> None:
        all_turns = self._turns
        if len(all_turns) < self._min_turns:
            return

        full_text = " ".join(t for _, t in all_turns)
        service_type = _detect_service_type(full_text)
        if service_type is None:
            return

        user_text = " ".join(t for sp, t in all_turns if sp == "user")
        items = _extract_items(user_text, service_type)
        if not items:
            return

        agent_echoed = agent_closed = user_closed = False
        for speaker, text in all_turns:
            lower = text.lower()
            if speaker == "agent":
                if any(p in lower for p in _AGENT_ECHO_PHRASES):
                    agent_echoed = True
                if any(p in lower for p in _AGENT_FINAL_SUMMARY_PHRASES):
                    agent_closed = True
            elif speaker == "user" and any(p in lower for p in _USER_DONE_PHRASES):
                user_closed = True

        if not agent_echoed or not (user_closed or agent_closed):
            return

        last_agent_turns = [t for sp, t in all_turns[-3:] if sp == "agent"]
        still_collecting = ["what items", "what would you like", "what else",
                            "would you like to add", "anything to add"]
        if last_agent_turns and any(p in last_agent_turns[-1].lower() for p in still_collecting):
            return

        room = self._room_number or _extract_room_number(full_text) or "000"
        guest_info = _extract_guest_info(all_turns)

        item_key = f"{room}:{service_type.value}:{','.join(sorted(i.name for i in items))}"
        if item_key in self._created_keys or item_key in self._creating_keys:
            return
        self._creating_keys.add(item_key)
        async with self._bill_lock:
            if item_key in self._created_keys:
                self._creating_keys.discard(item_key)
                return
            self._created_keys.add(item_key)
            self._creating_keys.discard(item_key)

        logger.info(
            "Bill triggered — service=%s room=%s items=%s",
            service_type.value, room, [(i.name, i.quantity) for i in items],
        )
        await self._create_bill_and_notify(service_type, room, items, guest_info, notes=user_text)

    async def _create_bill_and_notify(
        self,
        service_type: ServiceType,
        room_number: str,
        items: list[BillItem],
        guest_info: dict,
        notes: str = "",
    ) -> None:
        try:
            request = ServiceRequest(
                service_type=service_type,
                room_number=room_number,
                guest_name=guest_info["guest_name"],
                guest_phone=guest_info["guest_phone"],
                guest_email=guest_info["guest_email"],
                items=items,
                notes=notes[:200],
            )

            bill_gen = self._get_bill_generator()
            # create_bill does sync sqlite work -> keep it off the event loop
            bill, created = await asyncio.to_thread(bill_gen.create_bill, request)

            payu = self._get_payu_client()
            payu.create_payment(bill)  # sync — only computes the hash/txn fields
            payment_link = payu.get_payment_page_url(bill)
            await asyncio.to_thread(bill_gen.update_payment_link, bill.order_id, payment_link)
            bill_text = bill_gen.format_bill_text(bill)

            logger.info("Bill ready — order=%s total=Rs%.2f link=%s", bill.order_id, bill.total, payment_link)
        except Exception:
            logger.exception("Failed to create bill/payment link")
            return

        if self._on_payment_ready:
            try:
                self._on_payment_ready(payment_link, bill_text, room_number)
            except Exception:
                logger.exception("on_payment_ready callback error")

        # Push the order to HubSpot (best-effort — must never block billing)
        await asyncio.to_thread(
            self._push_order_to_crm, service_type, room_number, items, guest_info, notes
        )

        # Send the payment link to the guest's phone + email, not just the
        # browser data channel.
        await asyncio.to_thread(
            self._notify_guest, guest_info, payment_link, bill_text, bill.total
        )

        task = asyncio.ensure_future(self._poll_for_confirmation(bill.order_id, room_number))
        self._poll_tasks[bill.order_id] = task

    # ── CRM push ─────────────────────────────────────────────────────────

    # payments.ServiceType values that don't map to CRM (crm/hubspot_client.py)
    # only knows about ("taxi", "laundry", "food_order", "maintenance",
    # "payment"). Rather than push a record with fabricated/missing fields
    # for room_cleaning, restaurant_booking, spa — or the wrong shape for
    # cab_booking — we map what has a clean mapping and skip the rest with
    # a clear log line.
    _CRM_SERVICE_TYPE_MAP = {
        ServiceType.FOOD_ORDER: "food_order",
        ServiceType.LAUNDRY: "laundry",
        ServiceType.CAB_BOOKING: "taxi",
    }

    def _push_order_to_crm(
        self,
        service_type: ServiceType,
        room_number: str,
        items: list[BillItem],
        guest_info: dict,
        notes: str,
    ) -> None:
        crm_service_type = self._CRM_SERVICE_TYPE_MAP.get(service_type)
        if crm_service_type is None:
            logger.info(
                "Skipping CRM push for service_type=%s — no HubSpot object type "
                "configured for it (see _CRM_SERVICE_TYPE_MAP)", service_type.value,
            )
            return

        items_payload = [{"name": i.name, "quantity": i.quantity, "unit_price": i.unit_price} for i in items]
        data = {
            "service_type": crm_service_type,
            "room_number": room_number,
            "items": items_payload,
            "special_notes": notes[:500],
            "urgency": "normal",
            "status": "pending",
            # taxi payload wants destination/pickup_time; we don't parse
            # those explicitly yet from a food/laundry-style order, so give
            # honest placeholders rather than guessing.
            "destination": guest_info.get("destination", ""),
            "pickup_time": guest_info.get("pickup_time", "now"),
            "delivery_deadline": guest_info.get("delivery_deadline", ""),
        }
        try:
            record = crm_push(data)
            logger.info("CRM record created for %s: id=%s", crm_service_type, record.get("id"))
        except HubSpotConfigError as e:
            logger.warning("CRM push skipped — HubSpot not configured: %s", e)
        except Exception:
            logger.exception("CRM push failed for %s", crm_service_type)

    def _sync_payment_to_crm(self, bill_row: dict, room_number: str, status: str) -> None:
        data = {
            "service_type": "payment",
            "room_number": room_number,
            "amount": bill_row.get("total"),
            "payment_method": "payu",
            "payment_status": status,
            "status": status,
        }
        try:
            record = crm_push(data)
            logger.info("CRM payment record created: id=%s status=%s", record.get("id"), status)
        except HubSpotConfigError as e:
            logger.warning("CRM payment push skipped — HubSpot not configured: %s", e)
        except Exception:
            logger.exception("CRM payment push failed")

    # ── Notifications ────────────────────────────────────────────────────

    def _notify_guest(self, guest_info: dict, payment_link: str, bill_text: str, total: float) -> None:
        guest_name = guest_info.get("guest_name", "Guest")
        phone = guest_info.get("guest_phone", "")
        email = guest_info.get("guest_email", "")

        sms_ok = send_sms(phone, {
            "VAR1": guest_name,
            "VAR2": f"{total:.2f}",
            "VAR3": payment_link,
        })
        if not sms_ok:
            logger.info("Payment-link SMS not sent (see notifications/sms.py docstring for setup)")

        email_ok = send_email(
            to_email=email,
            to_name=guest_name,
            subject="Your bill is ready — pay online",
            body=(
                f"Dear {guest_name},\n\n"
                f"{bill_text}\n\n"
                f"Pay securely here: {payment_link}\n\n"
                f"Thank you!"
            ),
        )
        if not email_ok:
            logger.info("Payment-link email not sent (check SENDGRID_* env vars)")

    async def _poll_for_confirmation(self, order_id: str, room_number: str) -> None:
        """
        Watches for the bill's status to flip away from 'pending'.

        Previously this called PayUClient.check_payment_status(order_id)
        every tick — a live network call to PayU's verify API, redundant
        with the fact that payments/webhook_handler.py's /payment/success
        and /payment/failure routes (hit directly by PayU) already call
        BillGenerator.update_bill_status() the moment payment resolves.

        The webhook is the actual source of truth. This just watches the
        same SQLite row it already writes to
        (bill_generator.get_bill_by_order_id), which is cheap, local, and
        has no dependency on PayU's API being reachable a second time.

        NOTE — process topology: the webhook runs in the token-api
        container; this runs in the agent-worker container. They only
        share state through the SQLite file at DB_PATH, which must be
        volume-mounted into BOTH containers (see docker-compose.yml).
        This is still a poll loop, just a local, near-zero-cost one —
        not a push. A true push (no polling at all) would need the
        webhook to call LiveKit's server API directly, or a pub/sub layer
        like Redis; either is a bigger architecture change than this fix.
        """
        max_attempts = int(3600 / LOCAL_STATUS_POLL_SECS)
        bill_gen = self._get_bill_generator()

        for attempt in range(max_attempts):
            await asyncio.sleep(LOCAL_STATUS_POLL_SECS)
            try:
                row = await asyncio.to_thread(bill_gen.get_bill_by_order_id, order_id)
            except Exception:
                logger.warning("Local status read error (attempt %d) for %s", attempt + 1, order_id)
                continue

            if row is None:
                logger.warning("Bill %s disappeared from DB while polling", order_id)
                return

            status = (row.get("status") or "").lower()

            if status == PaymentStatus.SUCCESS.value:
                if self._on_payment_confirmed:
                    try:
                        self._on_payment_confirmed(order_id, str(row.get("total", "")), room_number)
                    except Exception:
                        logger.exception("on_payment_confirmed callback error")
                await asyncio.to_thread(self._sync_payment_to_crm, row, room_number, "paid")
                return

            if status in ("failed", "cancelled"):
                await asyncio.to_thread(self._sync_payment_to_crm, row, room_number, status)
                return

        logger.warning("Payment confirmation wait timed out for order=%s", order_id)

