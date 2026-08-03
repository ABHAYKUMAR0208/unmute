"""
router.py — The HTTP surface of the worker, as a mountable APIRouter.

    from fastapi import FastAPI
    from payu_worker import create_router, PayuWorkerSettings

    app = FastAPI()
    app.include_router(create_router(PayuWorkerSettings()))

Design principles applied here:
  * No endpoint can crash the process. Every handler is wrapped so that
    unexpected errors become a clean JSON 500 instead of an unhandled
    exception (FastAPI would already catch these at the ASGI level and
    return a 500 too, but this keeps the response shape consistent and
    the error logged with context).
  * Sync DB calls (sqlite3) never run directly on the event loop — they
    go through `run_in_threadpool` so one slow DB write can't stall every
    other in-flight request.
  * `/api/*` endpoints require an API key (`X-API-Key` header) whenever
    `settings.api_key` is set. If it's not set, the router still works
    (for local dev) but logs a loud warning on every request.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ValidationError

from .bill_generator import BillGenerator, BillStorageError
from .config import PayuWorkerSettings
from .models import Bill, BillItem, PaymentStatus, ServiceRequest
from .payu_client import PayUClient, PayUConfigError
from .webhook_handler import WebhookHandler

logger = logging.getLogger("payu_worker.router")


class RefundRequest(BaseModel):
    payu_txn_id: str
    order_id: str
    amount: float | None = None  # optional — defaults to full bill total


def create_router(
    settings: PayuWorkerSettings,
    on_payment_success=None,
    on_payment_failure=None,
) -> APIRouter:
    problems = settings.validate()
    for p in problems:
        logger.warning("Config issue: %s", p)
    if not settings.api_key:
        logger.warning(
            "PAYU_WORKER_API_KEY is not set — /api/* endpoints are UNAUTHENTICATED. "
            "Fine for local dev, not for anything reachable from the internet."
        )

    bill_generator = BillGenerator(settings)
    payu_client: PayUClient | None = None
    payu_error: str | None = None
    try:
        payu_client = PayUClient(settings)
    except PayUConfigError as e:
        payu_error = str(e)
        logger.warning("PayU client not initialized: %s — payment endpoints will 503 until fixed", e)

    webhook_handler = None
    if payu_client:
        webhook_handler = WebhookHandler(
            payu_client=payu_client,
            bill_generator=bill_generator,
            on_payment_success=on_payment_success,
            on_payment_failure=on_payment_failure,
        )

    router = APIRouter()

    # ── Auth dependency ──────────────────────────────────────────────────

    async def require_api_key(x_api_key: str = Header(default="")):
        if settings.api_key and x_api_key != settings.api_key:
            raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")

    def require_payu() -> PayUClient:
        if payu_client is None:
            raise HTTPException(
                status_code=503,
                detail=f"PayU is not configured on this server: {payu_error}",
            )
        return payu_client

    # ── Helpers ──────────────────────────────────────────────────────────

    async def _safe(fn, *args, **kwargs):
        """Run a sync bill_generator call off the event loop, translate storage errors to 503."""
        try:
            return await run_in_threadpool(fn, *args, **kwargs)
        except BillStorageError as e:
            logger.error("Storage error: %s", e)
            raise HTTPException(status_code=503, detail="Storage temporarily unavailable") from e

    # ══════════════════════════════════════════════════════════════════
    #  BILLING
    # ══════════════════════════════════════════════════════════════════

    @router.post("/api/create-bill", dependencies=[Depends(require_api_key)])
    async def create_bill(request: ServiceRequest):
        client = require_payu()
        try:
            bill, created = await _safe(bill_generator.create_bill, request)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=str(e))

        if created:
            try:
                payment_data = client.create_payment(bill)
                payment_link = client.get_payment_page_url(bill)
                await _safe(bill_generator.update_payment_link, bill.order_id, payment_link)
                bill.payment_link = payment_link
            except Exception:
                logger.exception("Failed to create PayU payment for bill %s", bill.order_id)
                raise HTTPException(status_code=502, detail="Failed to create payment link")
        else:
            payment_data = client.create_payment(bill)

        bill_text = bill_generator.format_bill_text(bill)

        return {
            "success": True,
            "duplicate_of_pending": not created,
            "bill": bill.model_dump(),
            "payment_link": bill.payment_link or client.get_payment_page_url(bill),
            "bill_text": bill_text,
            "payu_data": payment_data.model_dump(),
        }

    @router.post("/api/bill/{order_id}/cancel", dependencies=[Depends(require_api_key)])
    async def cancel_bill(order_id: str, reason: str = ""):
        cancelled = await _safe(bill_generator.cancel_bill, order_id, reason)
        if not cancelled:
            raise HTTPException(status_code=404, detail="No pending bill with that order_id")
        return {"success": True, "order_id": order_id, "status": "cancelled"}

    @router.get("/api/bill/{order_id}", dependencies=[Depends(require_api_key)])
    async def get_bill(order_id: str):
        bill = await _safe(bill_generator.get_bill_by_order_id, order_id)
        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found")
        return bill

    @router.get("/api/bills/{room_number}", dependencies=[Depends(require_api_key)])
    async def get_room_bills(room_number: str):
        bills = await _safe(bill_generator.get_bills_by_room, room_number)
        return {"room_number": room_number, "bills": bills, "count": len(bills)}

    @router.get("/api/unpaid-bills", dependencies=[Depends(require_api_key)])
    async def get_unpaid_bills(room: str | None = None):
        bills = await _safe(bill_generator.get_unpaid_bills, room)
        total_due = round(sum(b["total"] for b in bills), 2)
        return {"bills": bills, "count": len(bills), "total_due": total_due}

    # ══════════════════════════════════════════════════════════════════
    #  PAYMENT PAGE (guest-facing, no API key — this link goes to guests)
    # ══════════════════════════════════════════════════════════════════

    @router.get("/pay/{order_id}", response_class=HTMLResponse)
    async def payment_page(order_id: str):
        client = require_payu()
        bill_data = await _safe(bill_generator.get_bill_by_order_id, order_id)
        if not bill_data:
            return HTMLResponse("<h1>Bill not found</h1>", status_code=404)

        if bill_data["status"] == PaymentStatus.SUCCESS.value:
            return HTMLResponse(f"<h1>✅ Already Paid</h1><p>Order {order_id} has already been paid.</p>")

        if bill_data["status"] in (PaymentStatus.CANCELLED.value, PaymentStatus.EXPIRED.value):
            return HTMLResponse(
                f"<h1>This order is no longer valid</h1>"
                f"<p>Order {order_id} was {bill_data['status']}. Please ask staff for a new bill.</p>",
                status_code=410,
            )

        items_list = json.loads(bill_data["items_json"])
        bill = Bill(
            bill_id=bill_data["bill_id"], order_id=bill_data["order_id"],
            service_type=bill_data["service_type"], room_number=bill_data["room_number"],
            guest_name=bill_data["guest_name"], guest_phone=bill_data["guest_phone"],
            guest_email=bill_data["guest_email"],
            items=[BillItem(**item) for item in items_list],
            subtotal=bill_data["subtotal"], tax_rate=bill_data["tax_rate"],
            tax_amount=bill_data["tax_amount"], total=bill_data["total"],
        )

        payment_data = client.create_payment(bill)
        payu_url = client.get_payment_url()

        items_html = "<br>".join(
            f"&nbsp;&nbsp;• {i.name} × {i.quantity} = ₹{i.total:.0f}" for i in bill.items
        )
        html = f"""<!DOCTYPE html>
<html><head><title>Payment — {settings.hotel_name}</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body{{font-family:-apple-system,sans-serif;background:#0d0d0d;color:#e8e8e8;display:flex;
flex-direction:column;align-items:center;justify-content:center;min-height:100vh;margin:0}}
.card{{background:#161616;border:1px solid #2a2a2a;border-radius:12px;padding:32px;
max-width:420px;width:90%;text-align:center}}
h2{{margin:0 0 8px 0;font-size:18px}}
.amount{{font-size:36px;font-weight:bold;color:#4a9eff;margin:16px 0}}
.details{{font-size:13px;color:#888;line-height:1.8;text-align:left;margin:16px 0}}
.spinner{{border:3px solid #2a2a2a;border-top:3px solid #4a9eff;border-radius:50%;
width:24px;height:24px;animation:spin 1s linear infinite;margin:16px auto}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.redirect-text{{font-size:12px;color:#555}}
button{{background:#4a9eff;color:white;border:none;padding:14px 32px;border-radius:8px;
font-size:16px;cursor:pointer;margin-top:16px}}
</style></head>
<body><div class="card">
<h2>{settings.hotel_name}</h2>
<p style="color:#888">Room {bill.room_number}</p>
<div class="amount">₹{bill.total:.2f}</div>
<div class="details">
<strong>Order:</strong> {bill.order_id}<br>
<strong>Service:</strong> {bill.service_type.value.replace('_', ' ').title()}<br>
<strong>Guest:</strong> {bill.guest_name}<br>
<strong>Items:</strong><br>{items_html}<br><br>
<strong>Subtotal:</strong> ₹{bill.subtotal:.2f}<br>
<strong>GST ({bill.tax_rate*100:.0f}%):</strong> ₹{bill.tax_amount:.2f}<br>
</div>
<div class="spinner"></div>
<p class="redirect-text">Redirecting to secure payment...</p>
<form id="payuForm" method="POST" action="{payu_url}">
<input type="hidden" name="key" value="{payment_data.merchant_key}">
<input type="hidden" name="txnid" value="{payment_data.txn_id}">
<input type="hidden" name="amount" value="{payment_data.amount}">
<input type="hidden" name="productinfo" value="{payment_data.product_info}">
<input type="hidden" name="firstname" value="{payment_data.firstname}">
<input type="hidden" name="email" value="{payment_data.email}">
<input type="hidden" name="phone" value="{payment_data.phone}">
<input type="hidden" name="surl" value="{payment_data.surl}">
<input type="hidden" name="furl" value="{payment_data.furl}">
<input type="hidden" name="hash" value="{payment_data.hash}">
<input type="hidden" name="udf1" value="{payment_data.udf1}">
<input type="hidden" name="udf2" value="{payment_data.udf2}">
<input type="hidden" name="udf3" value="{payment_data.udf3}">
<noscript><button type="submit">Pay ₹{bill.total:.2f}</button></noscript>
</form>
</div>
<script>setTimeout(() => document.getElementById('payuForm').submit(), 2000);</script>
</body></html>"""
        return HTMLResponse(html)

    # ══════════════════════════════════════════════════════════════════
    #  PAYU WEBHOOK CALLBACKS (PayU calls these — no API key; protected by hash)
    # ══════════════════════════════════════════════════════════════════

    @router.post("/payment/success")
    async def payment_success(request: Request):
        if webhook_handler is None:
            raise HTTPException(status_code=503, detail="PayU is not configured")
        form_data = await request.form()
        data = dict(form_data)
        logger.info("PayU SUCCESS callback received: txn=%s", data.get("txnid"))
        result = await run_in_threadpool(webhook_handler.process_success, data)

        if result["success"]:
            return HTMLResponse(f"""<!DOCTYPE html><html><head><title>Payment Successful</title>
<style>body{{font-family:sans-serif;background:#0d0d0d;color:#e8e8e8;display:flex;
align-items:center;justify-content:center;min-height:100vh}}
.card{{background:#161616;border:1px solid #1a5c35;border-radius:12px;padding:40px;
text-align:center;max-width:400px}}.check{{font-size:64px}}h2{{color:#34d47a}}
.detail{{color:#888;font-size:13px;margin-top:12px;line-height:1.8}}</style></head>
<body><div class="card"><div class="check">✅</div><h2>Payment Successful!</h2>
<p>₹{result.get('amount','')}</p><div class="detail">
Order: {result.get('txn_id','')}<br>Room: {result.get('room_number','')}<br>
Transaction: {result.get('mihpayid','')}<br></div>
<p style="color:#555;font-size:12px;margin-top:20px">You can close this page.</p>
</div></body></html>""")
        return HTMLResponse(
            f"<h1>Payment verification failed</h1><p>{result.get('error', '')}</p>", status_code=400
        )

    @router.post("/payment/failure")
    async def payment_failure(request: Request):
        if webhook_handler is None:
            raise HTTPException(status_code=503, detail="PayU is not configured")
        form_data = await request.form()
        data = dict(form_data)
        logger.info("PayU FAILURE callback received: txn=%s", data.get("txnid"))
        result = await run_in_threadpool(webhook_handler.process_failure, data)

        return HTMLResponse(f"""<!DOCTYPE html><html><head><title>Payment Failed</title>
<style>body{{font-family:sans-serif;background:#0d0d0d;color:#e8e8e8;display:flex;
align-items:center;justify-content:center;min-height:100vh}}
.card{{background:#161616;border:1px solid #5c1a1a;border-radius:12px;padding:40px;
text-align:center;max-width:400px}}.icon{{font-size:64px}}h2{{color:#d43434}}
.detail{{color:#888;font-size:13px;margin-top:12px}}a{{color:#4a9eff;text-decoration:none}}
</style></head><body><div class="card"><div class="icon">❌</div><h2>Payment Failed</h2>
<div class="detail">Order: {result.get('txn_id','')}<br>Error: {result.get('error', 'Unknown')}<br></div>
<p style="margin-top:20px"><a href="/pay/{result.get('txn_id','')}">Try Again</a></p>
</div></body></html>""")

    # ══════════════════════════════════════════════════════════════════
    #  STATUS & REFUND
    # ══════════════════════════════════════════════════════════════════

    @router.get("/api/payment-status/{txn_id}", dependencies=[Depends(require_api_key)])
    async def payment_status(txn_id: str):
        client = require_payu()
        try:
            return await client.check_payment_status(txn_id)
        except Exception:
            logger.exception("check_payment_status failed for %s", txn_id)
            raise HTTPException(status_code=502, detail="Could not reach PayU")

    @router.post("/api/refund", dependencies=[Depends(require_api_key)])
    async def refund_payment(body: RefundRequest):
        client = require_payu()
        bill = await _safe(bill_generator.get_bill_by_order_id, body.order_id)
        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found")
        if bill["status"] != PaymentStatus.SUCCESS.value:
            raise HTTPException(status_code=400, detail=f"Bill is '{bill['status']}', not paid — nothing to refund")

        # Never trust a caller-supplied amount blindly: cap to what was
        # actually billed and paid, so a bad client can't drain more than
        # the guest was charged.
        max_refundable = float(bill["total"])
        amount = body.amount if body.amount is not None else max_refundable
        if amount <= 0 or amount > max_refundable + 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"amount must be between 0 and {max_refundable:.2f} (the billed total)",
            )

        try:
            result = await client.initiate_refund(body.payu_txn_id, body.order_id, amount)
        except Exception:
            logger.exception("Refund call to PayU failed for order_id=%s", body.order_id)
            raise HTTPException(status_code=502, detail="Could not reach PayU to process refund")

        if result.get("status") == 1:
            await _safe(bill_generator.update_bill_status, body.order_id, PaymentStatus.REFUNDED)
        return result

    # ══════════════════════════════════════════════════════════════════
    #  UTILITY
    # ══════════════════════════════════════════════════════════════════

    @router.get("/health")
    async def health():
        config_problems = settings.validate()
        return {
            "status": "ok" if not config_problems else "degraded",
            "service": "payu-worker",
            "payu_mode": settings.payu_mode,
            "payu_configured": payu_client is not None,
            "issues": config_problems,
        }

    @router.get("/api/maintenance/expire-stale-bills", dependencies=[Depends(require_api_key)])
    async def run_expiry_sweep():
        """Manually trigger the stale-bill sweep (also runs automatically in the background)."""
        count = await _safe(bill_generator.expire_stale_pending_bills)
        return {"expired": count}

    return router
