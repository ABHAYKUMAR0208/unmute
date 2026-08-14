"""
worker.py
---------
Standalone CRM worker. Watches transcripts/unprocessed/ for transcripts
whose call has actually ended (see get_next_ready_file), extracts one or
more service requests from each, validates them independently, pushes
each valid one to HubSpot (plus billing), logs the transcript once, and
saves a local JSON copy per service for the dashboard API to read.

Files are produced by app/transcript_writer.py's TranscriptWriter class,
named <room_name>.jsonl. Completion is signalled by a matching
<room_name>.done sentinel, written by TranscriptWriter.mark_complete()
from the agent's LiveKit shutdown callback — not by file-quiet timing.
A stale-file fallback (crm_stale_after_seconds) still exists for the case
where the agent process crashes before it can write the sentinel.

A single transcript can contain more than one distinct service request
(e.g. food + taxi in one call) — extract_from_file() returns a list, one
dict per service. Each is validated and pushed independently: a malformed
service doesn't block a correctly-extracted one in the same call. The
whole file is only sent to failed/ if literally none of the extracted
services validated.

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
from .validator import validate_all
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


def _done_path(jsonl_path: Path) -> Path:
    return jsonl_path.with_suffix(".done")


def get_next_ready_file() -> tuple[Path, bool] | None:
    """
    Returns (path, is_fallback) for the first .jsonl file that's ready to
    process, or None if nothing's ready yet.

    Primary signal: a matching <room>.done sentinel exists — written by
    TranscriptWriter.mark_complete() once the LiveKit job actually ends.

    Fallback: if a .jsonl has sat untouched for much longer than any real
    call would take (crm_stale_after_seconds) with no .done file ever
    appearing, process it anyway — covers the agent process crashing
    before its shutdown callback can run. is_fallback=True is returned so
    the caller can log this distinctly; it should be rare.
    """
    candidates = sorted(UNPROCESSED_DIR.glob("*.jsonl"))

    for path in candidates:
        if _done_path(path).exists():
            return path, False

    for path in candidates:
        age = time.time() - path.stat().st_mtime
        if age >= settings.crm_stale_after_seconds:
            return path, True

    return None


def _move_with_sentinel(transcript_path: Path, dest_dir: Path) -> None:
    """Moves the .jsonl and, if present, its .done sentinel alongside it."""
    shutil.move(str(transcript_path), dest_dir / transcript_path.name)
    done_path = _done_path(transcript_path)
    if done_path.exists():
        shutil.move(str(done_path), dest_dir / done_path.name)


def save_dashboard_copy(service: dict, index: int) -> Path:
    """
    Saves one validated+pushed service locally as JSON, so the dashboard
    API (crm_router.py) can list/display it without touching HubSpot.
    Filename includes the service's index and type so multiple services
    from the same call (same session_id) never collide on disk.
    """
    session_id = service.get("session_id") or "unknown"
    service_type = service.get("service_type") or "unknown"
    out_path = CRM_OUTPUTS_DIR / f"{session_id}_{index}_{service_type}_crm.json"
    payload = {
        **service,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Dashboard copy saved -> %s", out_path)
    return out_path


def process_file(transcript_path: Path, is_fallback: bool = False) -> None:
    logger.info("Processing: %s%s", transcript_path, " [FALLBACK — no .done sentinel found]" if is_fallback else "")
    if is_fallback:
        logger.warning(
            "Processing %s via stale-file fallback, not its completion sentinel. "
            "This usually means the agent process didn't shut down cleanly for this "
            "call — worth checking agent-worker logs around this time.",
            transcript_path.name,
        )

    try:
        logger.info("[1/4] Extracting from transcript...")
        services = extract_from_file(str(transcript_path))
        logger.info("Extracted %d service(s) from this transcript", len(services))

        if not services:
            logger.warning("Extraction returned no services at all.")
            _move_with_sentinel(transcript_path, FAILED_DIR)
            return

        logger.info("[2/4] Validating each service independently...")
        results = validate_all(services)
        for service, is_valid, errors in results:
            if is_valid:
                logger.info("  VALID   %s", service.get("service_type"))
            else:
                logger.warning("  INVALID %s -- %s", service.get("service_type"), errors)

        valid_services = [service for service, is_valid, _ in results if is_valid]

        if not valid_services:
            logger.warning("None of the %d extracted service(s) validated. Moving to failed/.", len(services))
            _move_with_sentinel(transcript_path, FAILED_DIR)
            return

        logger.info(
            "[3/4] Pushing %d/%d valid service(s) to HubSpot (+ billing)...",
            len(valid_services), len(services),
        )
        for i, service in enumerate(valid_services):
            record = hubspot_client.push(service)
            logger.info("  HubSpot record created for %s. ID: %s", service.get("service_type"), record.get("id"))

            save_dashboard_copy({**service, "hubspot_record_id": record.get("id")}, i)

            bill_result = create_bill_from_crm_data(service)
            if bill_result:
                logger.info(
                    "  Bill created for %s: order=%s total=Rs%.2f link=%s",
                    service.get("service_type"), bill_result["order_id"],
                    bill_result["total"], bill_result["payment_link"],
                )
            else:
                logger.info(
                    "  No bill created for %s (not billable, missing fields, "
                    "or no catalog price match — see billing_service.py logs above)",
                    service.get("service_type"),
                )

        logger.info("[4/4] Logging transcript to HubSpot...")
        # One transcript log per file, not per service — summarize across
        # every VALID service (room/session/timestamp are shared; service
        # types are combined into one comma-separated string).
        first = valid_services[0]
        summary = {
            "session_id": first.get("session_id"),
            "room_number": first.get("room_number"),
            "room_name": first.get("room_name"),
            "timestamp": first.get("timestamp"),
            "service_type": ", ".join(sorted({s.get("service_type", "") for s in valid_services})),
        }
        hubspot_client.push_transcript_log(summary, str(transcript_path))

        if len(valid_services) < len(services):
            logger.warning(
                "%d/%d service(s) failed validation and were skipped — see [2/4] log above for details. "
                "File still counted as processed since at least one service succeeded.",
                len(services) - len(valid_services), len(services),
            )

        _move_with_sentinel(transcript_path, PROCESSED_DIR)
        logger.info("Moved to processed/")

    except Exception as exc:
        logger.error("Error processing %s: %s", transcript_path, exc, exc_info=True)
        _move_with_sentinel(transcript_path, FAILED_DIR)
        logger.info("Moved to failed/")


def run_forever() -> None:
    _ensure_dirs()
    logger.info("CRM worker started. Watching %s", UNPROCESSED_DIR)
    while True:
        result = get_next_ready_file()
        if result:
            path, is_fallback = result
            logger.info("Ready to process: %s", path)
            process_file(path, is_fallback=is_fallback)
        else:
            time.sleep(settings.crm_poll_interval)


if __name__ == "__main__":
    run_forever()
