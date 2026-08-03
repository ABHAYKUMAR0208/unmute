"""
bill_generator.py — Creates and stores itemized bills.

Hardening vs. a naive version:
  * Every DB call goes through a context-managed connection with WAL mode
    + a busy_timeout, so concurrent requests don't crash with
    "database is locked".
  * All DB errors are caught and re-raised as `BillStorageError` — a
    known, catchable exception type instead of a raw sqlite3.Error
    bubbling up into a 500 with a stack trace.
  * `create_bill` is idempotent: an identical request (same room, service,
    items, guest) repeated within `dedupe_window_seconds` returns the
    existing pending bill instead of creating a new one. This is what
    prevents the "guest gets billed 10x because the client retried"
    class of bug.
  * `expire_stale_pending_bills` lets a background sweep (see
    maintenance.py) auto-cancel abandoned bills so they never inflate an
    "amount due" total for a room.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .config import PayuWorkerSettings
from .models import Bill, BillItem, PaymentStatus, ServiceRequest

logger = logging.getLogger("payu_worker.bill_generator")

DEFAULT_TAX_RATES = {
    "food_order": 0.05,
    "room_cleaning": 0.18,
    "cab_booking": 0.05,
    "restaurant_booking": 0.05,
    "laundry": 0.18,
    "spa": 0.18,
    "default": 0.18,
}


class BillStorageError(RuntimeError):
    """Raised when a DB operation fails. Always safe to catch and turn into a 5xx."""


class BillGenerator:
    """
    Creates and stores hotel/service bills.

        settings = PayuWorkerSettings()
        generator = BillGenerator(settings)
        bill = generator.create_bill(service_request)
    """

    def __init__(self, settings: PayuWorkerSettings, tax_rates: dict[str, float] | None = None):
        self.settings = settings
        self.tax_rates = tax_rates or DEFAULT_TAX_RATES
        self._init_db()

    # ── Connection handling ─────────────────────────────────────────────

    @contextmanager
    def _conn(self):
        Path(self.settings.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.settings.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=10000;")
            conn.execute("PRAGMA foreign_keys=ON;")
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logger.error("DB error: %s", e)
            raise BillStorageError(str(e)) from e
        finally:
            conn.close()

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS bills (
                    bill_id           TEXT PRIMARY KEY,
                    order_id          TEXT UNIQUE NOT NULL,
                    service_type      TEXT NOT NULL,
                    room_number       TEXT NOT NULL,
                    guest_name        TEXT NOT NULL,
                    guest_phone       TEXT NOT NULL,
                    guest_email       TEXT NOT NULL,
                    items_json        TEXT NOT NULL,
                    subtotal          REAL NOT NULL,
                    tax_rate          REAL NOT NULL,
                    tax_amount        REAL NOT NULL,
                    total             REAL NOT NULL,
                    currency          TEXT DEFAULT 'INR',
                    status            TEXT DEFAULT 'pending',
                    payment_link      TEXT DEFAULT '',
                    payu_txn_id       TEXT DEFAULT '',
                    notes             TEXT DEFAULT '',
                    idempotency_key   TEXT DEFAULT '',
                    created_at        TEXT NOT NULL,
                    paid_at           TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_bills_order_id ON bills(order_id);
                CREATE INDEX IF NOT EXISTS idx_bills_room ON bills(room_number);
                CREATE INDEX IF NOT EXISTS idx_bills_status ON bills(status);
                CREATE INDEX IF NOT EXISTS idx_bills_idempotency ON bills(idempotency_key);
            """)
        logger.info("BillGenerator DB ready: %s", self.settings.db_path)

    # ── Idempotency ──────────────────────────────────────────────────────

    @staticmethod
    def _derive_idempotency_key(request: ServiceRequest) -> str:
        """
        Stable fingerprint of "what is being ordered", independent of
        timestamp/order_id. Used to detect blind retries.
        """
        payload = {
            "room": request.room_number,
            "service": request.service_type.value,
            "guest": request.guest_phone,
            "items": sorted(
                [(i.name.lower(), i.quantity, i.unit_price) for i in request.items]
            ),
        }
        raw = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:24]

    def _find_recent_duplicate(self, conn, idempotency_key: str) -> dict | None:
        cutoff = (
            datetime.now(timezone.utc) - timedelta(seconds=self.settings.dedupe_window_seconds)
        ).isoformat()
        row = conn.execute(
            """
            SELECT * FROM bills
            WHERE idempotency_key = ?
              AND status = 'pending'
              AND created_at >= ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (idempotency_key, cutoff),
        ).fetchone()
        return dict(row) if row else None

    # ── Bill creation ────────────────────────────────────────────────────

    def create_bill(self, request: ServiceRequest) -> tuple[Bill, bool]:
        """
        Create an itemized bill from a service request.

        Returns (bill, created) — created is False if an existing pending
        bill matched (duplicate request), True if a new one was inserted.
        """
        idempotency_key = request.idempotency_key or self._derive_idempotency_key(request)

        with self._conn() as conn:
            existing = self._find_recent_duplicate(conn, idempotency_key)
            if existing:
                logger.info(
                    "Duplicate create_bill suppressed — returning existing bill %s (room %s)",
                    existing["order_id"], existing["room_number"],
                )
                return self._row_to_bill(existing), False

            items = [
                BillItem(name=i.name, quantity=i.quantity, unit_price=i.unit_price)
                for i in request.items
            ]
            subtotal = round(sum(i.total for i in items), 2)
            tax_rate = self.tax_rates.get(request.service_type.value, self.tax_rates["default"])
            tax_amount = round(subtotal * tax_rate, 2)
            total = round(subtotal + tax_amount, 2)

            bill = Bill(
                service_type=request.service_type,
                room_number=request.room_number,
                guest_name=request.guest_name,
                guest_phone=request.guest_phone,
                guest_email=request.guest_email,
                items=items,
                subtotal=subtotal,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                total=total,
                notes=request.notes,
                idempotency_key=idempotency_key,
            )

            conn.execute(
                """
                INSERT INTO bills
                (bill_id, order_id, service_type, room_number, guest_name,
                 guest_phone, guest_email, items_json, subtotal, tax_rate,
                 tax_amount, total, currency, status, payment_link,
                 payu_txn_id, notes, idempotency_key, created_at, paid_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bill.bill_id, bill.order_id, bill.service_type.value,
                    bill.room_number, bill.guest_name, bill.guest_phone,
                    bill.guest_email,
                    json.dumps([item.model_dump() for item in bill.items]),
                    bill.subtotal, bill.tax_rate, bill.tax_amount, bill.total,
                    bill.currency, bill.status.value, bill.payment_link,
                    bill.payu_txn_id, bill.notes, bill.idempotency_key,
                    bill.created_at, bill.paid_at,
                ),
            )

        logger.info(
            "Bill created: %s | %s | Room %s | ₹%.2f",
            bill.bill_id, bill.service_type.value, bill.room_number, bill.total,
        )
        return bill, True

    @staticmethod
    def _row_to_bill(row: dict) -> Bill:
        items = [BillItem(**item) for item in json.loads(row["items_json"])]
        return Bill(
            bill_id=row["bill_id"],
            order_id=row["order_id"],
            service_type=row["service_type"],
            room_number=row["room_number"],
            guest_name=row["guest_name"],
            guest_phone=row["guest_phone"],
            guest_email=row["guest_email"],
            items=items,
            subtotal=row["subtotal"],
            tax_rate=row["tax_rate"],
            tax_amount=row["tax_amount"],
            total=row["total"],
            currency=row["currency"],
            status=row["status"],
            payment_link=row["payment_link"],
            payu_txn_id=row["payu_txn_id"],
            notes=row["notes"],
            idempotency_key=row.get("idempotency_key", ""),
            created_at=row["created_at"],
            paid_at=row["paid_at"],
        )

    # ── Status / lifecycle ───────────────────────────────────────────────

    def update_bill_status(self, order_id: str, status: PaymentStatus,
                            payu_txn_id: str = "", paid_at: str = "") -> bool:
        with self._conn() as conn:
            cur = conn.execute(
                "UPDATE bills SET status = ?, payu_txn_id = COALESCE(NULLIF(?, ''), payu_txn_id), "
                "paid_at = COALESCE(NULLIF(?, ''), paid_at) WHERE order_id = ?",
                (status.value, payu_txn_id, paid_at, order_id),
            )
            updated = cur.rowcount > 0
        if updated:
            logger.info("Bill %s updated → %s", order_id, status.value)
        else:
            logger.warning("update_bill_status: no bill found for order_id=%s", order_id)
        return updated

    def cancel_bill(self, order_id: str, reason: str = "") -> bool:
        """Explicitly cancel a pending bill (e.g. guest changed their order)."""
        with self._conn() as conn:
            cur = conn.execute(
                "UPDATE bills SET status = ?, notes = CASE WHEN ? != '' THEN ? ELSE notes END "
                "WHERE order_id = ? AND status = 'pending'",
                (PaymentStatus.CANCELLED.value, reason, reason, order_id),
            )
            return cur.rowcount > 0

    def expire_stale_pending_bills(self) -> int:
        """
        Mark pending bills older than pending_bill_ttl_minutes as EXPIRED.
        Meant to be called periodically (see maintenance.py). Returns the
        number of bills expired.
        """
        cutoff = (
            datetime.now(timezone.utc) - timedelta(minutes=self.settings.pending_bill_ttl_minutes)
        ).isoformat()
        with self._conn() as conn:
            cur = conn.execute(
                "UPDATE bills SET status = ? WHERE status = 'pending' AND created_at < ?",
                (PaymentStatus.EXPIRED.value, cutoff),
            )
            count = cur.rowcount
        if count:
            logger.info("Expired %d stale pending bill(s) older than %d min",
                        count, self.settings.pending_bill_ttl_minutes)
        return count

    def update_payment_link(self, order_id: str, payment_link: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE bills SET payment_link = ? WHERE order_id = ?",
                (payment_link, order_id),
            )

    # ── Reads ────────────────────────────────────────────────────────────

    def get_bill_by_order_id(self, order_id: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM bills WHERE order_id = ?", (order_id,)).fetchone()
            return dict(row) if row else None

    def get_bills_by_room(self, room_number: str) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM bills WHERE room_number = ? ORDER BY created_at DESC",
                (room_number,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_unpaid_bills(self, room_number: str | None = None) -> list[dict]:
        with self._conn() as conn:
            if room_number:
                rows = conn.execute(
                    "SELECT * FROM bills WHERE room_number = ? AND status = 'pending' "
                    "ORDER BY created_at DESC",
                    (room_number,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM bills WHERE status = 'pending' ORDER BY created_at DESC"
                ).fetchall()
            return [dict(r) for r in rows]

    # ── Presentation ─────────────────────────────────────────────────────

    def format_bill_text(self, bill: Bill) -> str:
        """Format a bill as readable text (e.g. for an AI agent to read to the guest)."""
        lines = [
            f"── {self.settings.hotel_name} ──",
            f"Bill #{bill.bill_id}",
            f"Room: {bill.room_number}  |  Guest: {bill.guest_name}",
            f"Service: {bill.service_type.value.replace('_', ' ').title()}",
            "",
            "Items:",
        ]
        for item in bill.items:
            lines.append(
                f"  {item.name:<30} {item.quantity}x ₹{item.unit_price:.0f}  = ₹{item.total:.2f}"
            )
        lines.extend([
            "",
            f"  {'Subtotal':<30}            ₹{bill.subtotal:.2f}",
            f"  {'GST @':<6}{bill.tax_rate*100:.0f}%{'':<24}₹{bill.tax_amount:.2f}",
            f"  {'TOTAL':<30}            ₹{bill.total:.2f}",
        ])
        if self.settings.hotel_gst_number:
            lines.extend(["", f"GST: {self.settings.hotel_gst_number}"])
        return "\n".join(lines)
