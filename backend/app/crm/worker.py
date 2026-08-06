"""
worker.py
---------
Standalone CRM worker. Polls transcripts/unprocessed/ for finished-call
transcript files, extracts structured intent, validates it, pushes it to
HubSpot, and also saves a local JSON copy for the dashboard API to read.

Files are produced by app/transcript_writer.py's TranscriptWriter class,
named <room_name>.jsonl. This worker only reads them — it owns no part of
turn-boundary detection or "call ended" logic; TranscriptWriter already
flushes complete turns per role-switch, and this worker's own quiet-period
check (same design as Personaplex's crm_worker.py) is what decides a call
is over and the file is ready to process.

Run:
    python -m app.crm.worker
"""

from __future__ import annotations

import json
import logging
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

from ..config import settings
from . import hubspot_client
from .extractor import extract_from_file
from .validator import validate
from ..payments.billing_service import create_bill_from_crm_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crm.worker")

TRANSCRIPTS_DIR = Path(settings.crm_transcripts_dir)
UNPROCESSED_DIR = TRANSCRIPTS_DIR / "unprocessed"
PROCESSED_DIR = TRANSCRIPTS_DIR / "processed"
FAILED_DIR = TRANSCRIPTS_DIR / "failed"
CRM_OUTPUTS_DIR = Path(settings.crm_outputs_dir)


def _ensure_dirs() -> None:
    for d in (UNPROCESSED_DIR, PROCESSED_DIR, FAILED_DIR, CRM_OUTPUTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def get_next_file() -> Path | None:
    """Returns the first .jsonl file found in unprocessed/, or None."""
    files = sorted(p for p in UNPROCESSED_DIR.glob("*.jsonl"))
    return files[0] if files else None


def wait_for_call_to_end(path: Path) -> None:
    """
    Polls the file's last-modified time. Returns once the file has not
    been modified for crm_quiet_period seconds (i.e. the call is over).
    """
    logger.info("Monitoring %s for inactivity (%ss quiet period)...", path, settings.crm_quiet_period)
    while True:
        last_modified = path.stat().st_mtime
        time.sleep(settings.crm_quiet_period)
        if path.stat().st_mtime == last_modified:
            logger.info("File has been quiet. Assuming call has ended.")
            return


def save_dashboard_copy(data: dict) -> Path:
    """
    Saves the extracted+validated record locally as JSON, so the dashboard
    API (crm_router.py) can list/display it without touching HubSpot.
    Filename keys off session_id, which is populated with the room name
    (see extractor.py) — unique per call, same as Personaplex's session_id.
    """
    session_id = data.get("session_id") or "unknown"
    out_path = CRM_OUTPUTS_DIR / f"{session_id}_crm.json"
    payload = {
        **data,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Dashboard copy saved -> %s", out_path)
    return out_path


def process_file(transcript_path: Path) -> None:
    logger.info("Processing: %s", transcript_path)

    try:
        logger.info("[1/5] Extracting from transcript...")
        data = extract_from_file(str(transcript_path))
        logger.info(
            "Room: %s | Service: %s | Urgency: %s",
            data.get("room_number"), data.get("service_type"), data.get("urgency"),
        )

        logger.info("[2/5] Validating...")
        is_valid, errors = validate(data)
        if not is_valid:
            logger.warning("Validation failed: %s", errors)
            shutil.move(str(transcript_path), FAILED_DIR / transcript_path.name)
            return
        logger.info("Validation passed")

        logger.info("[3/5] Pushing to HubSpot...")
        record = hubspot_client.push(data)
        logger.info("HubSpot record created. ID: %s", record.get("id"))

        save_dashboard_copy({**data, "hubspot_record_id": record.get("id")})

        logger.info("[4/5] Creating PayU bill from CRM data...")
        bill_result = create_bill_from_crm_data(data)
        if bill_result:
            logger.info(
                "Bill created from CRM data: order=%s total=Rs%.2f link=%s",
                bill_result["order_id"], bill_result["total"], bill_result["payment_link"],
            )
        else:
            logger.info(
                "No bill created for this record (not a billable service_type, "
                "missing room number/items, or no catalog price match — see "
                "billing_service.py logs above for the exact reason)"
            )

        logger.info("[5/5] Logging transcript to HubSpot...")
        hubspot_client.push_transcript_log(data, str(transcript_path))

        shutil.move(str(transcript_path), PROCESSED_DIR / transcript_path.name)
        logger.info("Moved to processed/")

    except Exception as exc:
        logger.error("Error processing %s: %s", transcript_path, exc, exc_info=True)
        shutil.move(str(transcript_path), FAILED_DIR / transcript_path.name)
        logger.info("Moved to failed/")


def run_forever() -> None:
    _ensure_dirs()
    logger.info("CRM worker started. Watching %s", UNPROCESSED_DIR)
    while True:
        path = get_next_file()
        if path:
            logger.info("New file found: %s", path)
            wait_for_call_to_end(path)
            if path.exists():
                process_file(path)
        else:
            time.sleep(settings.crm_poll_interval)


if __name__ == "__main__":
    run_forever()