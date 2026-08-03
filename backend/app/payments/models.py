"""
models.py — Pydantic models for bills, payments, services.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class ServiceType(str, Enum):
    FOOD_ORDER = "food_order"
    ROOM_CLEANING = "room_cleaning"
    CAB_BOOKING = "cab_booking"
    RESTAURANT_BOOKING = "restaurant_booking"
    LAUNDRY = "laundry"
    SPA = "spa"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    INITIATED = "initiated"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


PHONE_RE = re.compile(r"^\+?\d{7,15}$")


class BillItem(BaseModel):
    """Single line item on a bill."""
    name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(default=1, gt=0, le=1000)
    unit_price: float = Field(ge=0, le=10_000_000)
    total: float = 0.0

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("item name cannot be blank")
        return v

    @model_validator(mode="after")
    def _compute_total(self) -> "BillItem":
        self.total = round(self.quantity * self.unit_price, 2)
        return self


class ServiceRequest(BaseModel):
    """Request from the caller (AI agent / front desk app / etc) to book a service."""
    service_type: ServiceType
    room_number: str = Field(min_length=1, max_length=20)
    guest_name: str = Field(min_length=1, max_length=200)
    guest_phone: str
    guest_email: str = "guest@hotel.com"
    items: list[BillItem] = Field(min_length=1, max_length=100)
    notes: str = Field(default="", max_length=1000)
    # Optional caller-supplied idempotency key. If omitted, the worker
    # derives one from (room, service, items, short time window) so that
    # blind retries don't create duplicate bills.
    idempotency_key: Optional[str] = None

    @field_validator("guest_phone")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not PHONE_RE.match(v):
            raise ValueError("guest_phone must be 7–15 digits, optionally prefixed with +")
        return v

    @field_validator("room_number", "guest_name")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class Bill(BaseModel):
    """Generated bill for a service."""
    bill_id: str = Field(default_factory=lambda: f"BILL-{uuid.uuid4().hex[:10].upper()}")
    order_id: str = Field(default_factory=lambda: f"ORD-{uuid.uuid4().hex[:12].upper()}")
    service_type: ServiceType
    room_number: str
    guest_name: str
    guest_phone: str
    guest_email: str
    items: list[BillItem]
    subtotal: float = 0.0
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    total: float = 0.0
    currency: str = "INR"
    status: PaymentStatus = PaymentStatus.PENDING
    payment_link: str = ""
    payu_txn_id: str = ""
    notes: str = ""
    idempotency_key: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    paid_at: Optional[str] = None


class PayUPaymentData(BaseModel):
    """Data needed to create a PayU payment."""
    merchant_key: str
    txn_id: str
    amount: str
    product_info: str
    firstname: str
    email: str
    phone: str
    surl: str
    furl: str
    hash: str
    udf1: str = ""
    udf2: str = ""
    udf3: str = ""
    udf4: str = ""
    udf5: str = ""


class PaymentWebhookData(BaseModel):
    """Data received from PayU webhook/redirect."""
    mihpayid: str = ""
    status: str = ""
    txnid: str = ""
    amount: str = ""
    productinfo: str = ""
    firstname: str = ""
    email: str = ""
    phone: str = ""
    hash: str = ""
    key: str = ""
    udf1: str = ""
    udf2: str = ""
    udf3: str = ""
    udf4: str = ""
    udf5: str = ""
    additional_charges: str = ""
    error_Message: str = ""
