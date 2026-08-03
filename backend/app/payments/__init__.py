"""
payu_worker — Drop-in PayU billing + payment worker for hotel/service apps.

Typical usage inside an existing FastAPI app:

    from fastapi import FastAPI
    from payu_worker import create_router, PayuWorkerSettings

    app = FastAPI()
    settings = PayuWorkerSettings()          # reads from env / .env
    app.include_router(create_router(settings), prefix="/payu")

Or run standalone: `python standalone_server.py`.
"""

from .config import PayuWorkerSettings
from .models import (
    ServiceType,
    PaymentStatus,
    BillItem,
    ServiceRequest,
    Bill,
)
from .bill_generator import BillGenerator
from .payu_client import PayUClient
from .webhook_handler import WebhookHandler
from .router import create_router
from .payment_bridge import PaymentBridge

__all__ = [
    "PayuWorkerSettings",
    "ServiceType",
    "PaymentStatus",
    "BillItem",
    "ServiceRequest",
    "Bill",
    "BillGenerator",
    "PayUClient",
    "WebhookHandler",
    "create_router",
    "PaymentBridge",
]

__version__ = "1.0.0"
