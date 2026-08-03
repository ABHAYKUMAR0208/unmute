"""
webhook_handler.py — Handles PayU payment callbacks (success/failure).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable, Optional

from .bill_generator import BillGenerator
from .models import PaymentStatus
from .payu_client import PayUClient

logger = logging.getLogger("payu_worker.webhook_handler")

AMOUNT_TOLERANCE = 0.01  # rupees; guards against float formatting drift


class WebhookHandler:
    """
    Processes PayU payment webhooks.

        handler = WebhookHandler(payu_client, bill_generator, on_payment_success=notify)
        result = handler.process_success(form_data)
    """

    def __init__(
        self,
        payu_client: PayUClient,
        bill_generator: BillGenerator,
        on_payment_success: Optional[Callable[[dict], None]] = None,
        on_payment_failure: Optional[Callable[[dict], None]] = None,
    ):
        self.payu_client = payu_client
        self.bill_generator = bill_generator
        self._on_success = on_payment_success
        self._on_failure = on_payment_failure

    def process_success(self, data: dict) -> dict:
        txn_id = data.get("txnid", "")
        mihpayid = data.get("mihpayid", "")
        status = data.get("status", "")
        amount = data.get("amount", "")
        product_info = data.get("productinfo", "")
        firstname = data.get("firstname", "")
        email = data.get("email", "")
        received_hash = data.get("hash", "")
        udf1 = data.get("udf1", "")
        udf2 = data.get("udf2", "")
        udf3 = data.get("udf3", "")
        udf4 = data.get("udf4", "")
        udf5 = data.get("udf5", "")
        additional_charges = data.get("additionalCharges", "") or data.get("additional_charges", "")

        if not txn_id:
            logger.warning("Webhook success callback missing txnid")
            return {"success": False, "error": "missing txnid", "txn_id": ""}

        # ── Step 1: verify PayU's signature ─────────────────────────────
        is_valid = self.payu_client.verify_webhook_hash(
            txn_id=txn_id, amount=amount, product_info=product_info,
            firstname=firstname, email=email, status=status, received_hash=received_hash,
            udf1=udf1, udf2=udf2, udf3=udf3, udf4=udf4, udf5=udf5,
            additional_charges=additional_charges,
        )
        if not is_valid:
            logger.error("HASH VERIFICATION FAILED for txn=%s — possible tampering!", txn_id)
            return {"success": False, "error": "Hash verification failed", "txn_id": txn_id}

        # ── Step 2: cross-check the amount PayU says was paid against
        #    what we actually billed. The hash proves the amount wasn't
        #    tampered with *in transit*, but not that it matches our bill —
        #    e.g. a stale/reused webhook for a different order.
        bill = self.bill_generator.get_bill_by_order_id(txn_id)
        if not bill:
            logger.error("Webhook success for unknown order_id=%s", txn_id)
            return {"success": False, "error": "unknown order_id", "txn_id": txn_id}

        try:
            paid_amount = float(amount)
        except (TypeError, ValueError):
            paid_amount = -1.0

        if abs(paid_amount - float(bill["total"])) > AMOUNT_TOLERANCE:
            logger.error(
                "Amount mismatch for txn=%s: billed=%.2f paid=%.2f — NOT marking as paid",
                txn_id, bill["total"], paid_amount,
            )
            return {
                "success": False,
                "error": "amount mismatch",
                "txn_id": txn_id,
                "billed": bill["total"],
                "paid": paid_amount,
            }

        if bill["status"] == PaymentStatus.SUCCESS.value:
            # Already processed (PayU can retry webhooks) — idempotent no-op.
            logger.info("Webhook success for already-paid order_id=%s — ignoring duplicate", txn_id)
            return {
                "success": True, "txn_id": txn_id, "mihpayid": mihpayid, "amount": amount,
                "bill_id": bill["bill_id"], "room_number": bill["room_number"],
                "service_type": bill["service_type"], "paid_at": bill["paid_at"],
                "duplicate": True,
            }

        # ── Step 3: mark paid ────────────────────────────────────────────
        paid_at = datetime.now(timezone.utc).isoformat()
        self.bill_generator.update_bill_status(
            order_id=txn_id, status=PaymentStatus.SUCCESS, payu_txn_id=mihpayid, paid_at=paid_at,
        )

        result = {
            "success": True,
            "txn_id": txn_id,
            "mihpayid": mihpayid,
            "amount": amount,
            "bill_id": bill["bill_id"],
            "room_number": bill["room_number"],
            "service_type": bill["service_type"],
            "paid_at": paid_at,
        }
        logger.info("✅ Payment SUCCESS — txn=%s amount=₹%s room=%s", txn_id, amount, bill["room_number"])

        if self._on_success:
            try:
                self._on_success(result)
            except Exception:
                logger.exception("on_payment_success callback raised — payment already recorded")

        return result

    def process_failure(self, data: dict) -> dict:
        txn_id = data.get("txnid", "")
        error_msg = data.get("error_Message", "Payment failed")

        if not txn_id:
            logger.warning("Webhook failure callback missing txnid")
            return {"success": False, "error": "missing txnid", "txn_id": ""}

        logger.warning("❌ Payment FAILED — txn=%s error=%s", txn_id, error_msg)
        self.bill_generator.update_bill_status(order_id=txn_id, status=PaymentStatus.FAILED)

        result = {
            "success": False,
            "txn_id": txn_id,
            "error": error_msg,
            "bill_id": data.get("udf1", ""),
            "room_number": data.get("udf2", ""),
        }

        if self._on_failure:
            try:
                self._on_failure(result)
            except Exception:
                logger.exception("on_payment_failure callback raised")

        return result
