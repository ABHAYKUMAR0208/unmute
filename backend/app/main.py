import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from livekit import api

from .config import settings
from .crm_router import router as crm_router
from .crm.hubspot_client import push as crm_push, HubSpotConfigError
from .payments import BillGenerator, PayuWorkerSettings, create_router
from .payments.maintenance import run_expiry_sweep_forever

logger = logging.getLogger("unmute.main")

payu_settings = PayuWorkerSettings()
_bg_tasks: list[asyncio.Task] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    problems = payu_settings.validate()
    for p in problems:
        logger.warning("PayU config issue: %s", p)

    bill_generator = BillGenerator(payu_settings)
    task = asyncio.create_task(run_expiry_sweep_forever(bill_generator))
    _bg_tasks.append(task)
    logger.info("PayU stale-bill expiry sweep started.")

    yield

    for t in _bg_tasks:
        t.cancel()


app = FastAPI(title="Unmute Voice Agent - Token API", lifespan=lifespan)

# Wide open for local/dev testing. Tighten allow_origins to your real
# frontend domain before going to production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def catch_all_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"error": "internal_server_error"})


def _sync_payment_success_to_crm(result: dict) -> None:
    try:
        record = crm_push({
            "service_type": "payment",
            "room_number": result.get("room_number", ""),
            "amount": result.get("amount"),
            "payment_method": "payu",
            "payment_status": "paid",
            "status": "paid",
        })
        logger.info("CRM payment record created (paid): id=%s txn=%s", record.get("id"), result.get("txn_id"))
    except HubSpotConfigError as e:
        logger.warning("CRM payment push skipped — HubSpot not configured: %s", e)
    except Exception:
        logger.exception("CRM payment push failed for txn=%s", result.get("txn_id"))


def _sync_payment_failure_to_crm(result: dict) -> None:
    try:
        record = crm_push({
            "service_type": "payment",
            "room_number": result.get("room_number", ""),
            "payment_method": "payu",
            "payment_status": "failed",
            "status": "failed",
        })
        logger.info("CRM payment record created (failed): id=%s txn=%s", record.get("id"), result.get("txn_id"))
    except HubSpotConfigError as e:
        logger.warning("CRM payment push skipped — HubSpot not configured: %s", e)
    except Exception:
        logger.exception("CRM payment push failed for txn=%s", result.get("txn_id"))


app.include_router(crm_router, prefix="/api")
app.include_router(create_router(
    payu_settings,
    on_payment_success=_sync_payment_success_to_crm,
    on_payment_failure=_sync_payment_failure_to_crm,
))
# NOTE: /health is provided by the PayU router above — it already reports
# {"status": "ok"|"degraded", "payu_configured": ..., "issues": [...]}.
# Do not add another @app.get("/health") here; FastAPI/Starlette matches
# routes in registration order, so a second one here would be silently
# unreachable, not an error.


@app.get("/token")
def get_token():
    """
    Mint a fresh LiveKit token + unique room name on every call. The
    frontend calls this right before connecting, so it never uses a
    stale token or reconnects into an already-existing room.
    """
    room_name = f"room-{uuid.uuid4().hex[:8]}"
    identity = f"user-{uuid.uuid4().hex[:6]}"

    token = (
        api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(identity)
        .with_name("Guest")
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )

    return {"token": token, "room": room_name, "url": settings.livekit_url}