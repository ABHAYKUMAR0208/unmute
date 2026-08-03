"""
payu_client.py — PayU payment hash generation and payment operations.

PayU Hash Formula:
    hash = SHA512(key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5||||||SALT)

Reverse Hash (for verification):
    hash = SHA512(salt|status||||||udf5|udf4|udf3|udf2|udf1|email|firstname|productinfo|amount|txnid|key)

Security note: the merchant salt must never be written to logs, error
messages, or exceptions. Every log line in this module is built to
include only non-secret fields — the raw hash *input* string (which
contains the salt) is deliberately never logged, even at DEBUG level.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Optional

import httpx

from .config import PayuWorkerSettings
from .models import Bill, PayUPaymentData

logger = logging.getLogger("payu_worker.payu_client")


class PayUConfigError(RuntimeError):
    """Raised when PayU credentials are missing/invalid at call time."""


class PayUClient:

    def __init__(self, settings: PayuWorkerSettings):
        self.settings = settings
        if not settings.payu_merchant_key or not settings.payu_merchant_salt:
            raise PayUConfigError(
                "PAYU_MERCHANT_KEY and PAYU_MERCHANT_SALT must be set. "
                "Get test credentials from: https://devguide.payu.in/"
            )
        self.merchant_key = settings.payu_merchant_key
        self.merchant_salt = settings.payu_merchant_salt
        logger.info(
            "PayUClient initialized — mode=%s key=%s",
            settings.payu_mode.upper(), settings.masked_key_preview(),
        )

    # ── Hash generation ──────────────────────────────────────────────────

    def _generate_hash(
        self, txn_id: str, amount: str, product_info: str, firstname: str, email: str,
        udf1: str = "", udf2: str = "", udf3: str = "", udf4: str = "", udf5: str = "",
    ) -> str:
        hash_string = (
            f"{self.merchant_key}|{txn_id}|{amount}|{product_info}|{firstname}|{email}"
            f"|{udf1}|{udf2}|{udf3}|{udf4}|{udf5}||||||{self.merchant_salt}"
        )
        hash_value = hashlib.sha512(hash_string.encode("utf-8")).hexdigest().lower()
        # Never log hash_string — it contains the merchant salt.
        logger.debug("Hash generated for txn=%s (amount=%s)", txn_id, amount)
        return hash_value

    def _generate_reverse_hash(
        self, txn_id: str, amount: str, product_info: str, firstname: str, email: str,
        status: str, udf1: str = "", udf2: str = "", udf3: str = "", udf4: str = "",
        udf5: str = "", additional_charges: str = "",
    ) -> str:
        parts = []
        if additional_charges:
            parts.append(additional_charges)
        parts += [
            self.merchant_salt, status, "", "", "", "", "", "",
            udf5, udf4, udf3, udf2, udf1, email, firstname,
            product_info, amount, txn_id, self.merchant_key,
        ]
        hash_string = "|".join(parts)
        # Never log hash_string — it contains the merchant salt.
        return hashlib.sha512(hash_string.encode("utf-8")).hexdigest().lower()

    # ── Payment creation ─────────────────────────────────────────────────

    def create_payment(self, bill: Bill) -> PayUPaymentData:
        txn_id = bill.order_id
        amount = f"{bill.total:.2f}"
        # Pipe is PayU's field delimiter — must never appear inside a value.
        product_info = f"{bill.service_type.value} Room {bill.room_number}".replace("|", "-")

        payment_hash = self._generate_hash(
            txn_id=txn_id, amount=amount, product_info=product_info,
            firstname=bill.guest_name, email=bill.guest_email,
            udf1=bill.bill_id, udf2=bill.room_number, udf3=bill.service_type.value,
        )

        payment_data = PayUPaymentData(
            merchant_key=self.merchant_key,
            txn_id=txn_id,
            amount=amount,
            product_info=product_info,
            firstname=bill.guest_name,
            email=bill.guest_email,
            phone=bill.guest_phone,
            surl=f"{self.settings.base_url}/payment/success",
            furl=f"{self.settings.base_url}/payment/failure",
            hash=payment_hash,
            udf1=bill.bill_id,
            udf2=bill.room_number,
            udf3=bill.service_type.value,
        )

        logger.info("Payment created: txn=%s amount=%s", txn_id, amount)
        return payment_data

    def get_payment_url(self) -> str:
        return self.settings.payu_base_url

    def get_payment_page_url(self, bill: Bill) -> str:
        return f"{self.settings.base_url}/pay/{bill.order_id}"

    # ── Webhook verification ─────────────────────────────────────────────

    def verify_webhook_hash(
        self, txn_id: str, amount: str, product_info: str, firstname: str, email: str,
        status: str, received_hash: str, udf1: str = "", udf2: str = "", udf3: str = "",
        udf4: str = "", udf5: str = "", additional_charges: str = "",
    ) -> bool:
        expected_hash = self._generate_reverse_hash(
            txn_id=txn_id, amount=amount, product_info=product_info,
            firstname=firstname, email=email, status=status,
            udf1=udf1, udf2=udf2, udf3=udf3, udf4=udf4, udf5=udf5,
            additional_charges=additional_charges,
        )
        is_valid = expected_hash == received_hash
        if not is_valid:
            logger.warning("Hash mismatch for txn=%s — possible tampering", txn_id)
        return is_valid

    # ── Payment status check (API) ───────────────────────────────────────

    async def check_payment_status(self, txn_id: str) -> dict:
        command = "verify_payment"
        hash_string = f"{self.merchant_key}|{command}|{txn_id}|{self.merchant_salt}"
        command_hash = hashlib.sha512(hash_string.encode("utf-8")).hexdigest().lower()

        payload = {"key": self.merchant_key, "command": command, "var1": txn_id, "hash": command_hash}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(self.settings.payu_verify_url, data=payload)
            response.raise_for_status()
            result = response.json()

        logger.info("Payment status for %s: %s", txn_id, result.get("status"))
        return result

    # ── Refund ────────────────────────────────────────────────────────────

    async def initiate_refund(self, payu_txn_id: str, txn_id: str, amount: float) -> dict:
        command = "cancel_refund_transaction"
        hash_string = f"{self.merchant_key}|{command}|{payu_txn_id}|{self.merchant_salt}"
        command_hash = hashlib.sha512(hash_string.encode("utf-8")).hexdigest().lower()

        payload = {
            "key": self.merchant_key,
            "command": command,
            "var1": payu_txn_id,
            "var2": txn_id,
            "var3": f"{amount:.2f}",
            "hash": command_hash,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(self.settings.payu_verify_url, data=payload)
            response.raise_for_status()
            result = response.json()

        logger.info("Refund result for %s: %s", txn_id, result.get("status"))
        return result
