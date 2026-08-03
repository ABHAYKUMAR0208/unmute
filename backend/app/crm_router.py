"""
crm_router.py — REST endpoints for CRM records.

Mounted onto the main FastAPI app under /api. Ported from Personaplex's
frontend/data_router.py — CRM section only.

Routes (all GET):
    /api/crm                → list all CRM JSON records
    /api/crm/{session_id}   → one CRM JSON record
"""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

from .config import settings

logger = logging.getLogger("crm_router")

CRM_OUTPUTS_DIR = Path(settings.crm_outputs_dir)

router = APIRouter()


@router.get("/crm")
def list_crm_records():
    if not CRM_OUTPUTS_DIR.exists():
        return {"records": []}

    records = []
    for path in sorted(CRM_OUTPUTS_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            records.append({"id": path.stem, "file": path.name, **data})
        except Exception as exc:
            logger.warning("Could not read CRM file %s: %s", path, exc)

    return {"records": records}


@router.get("/crm/{record_id}")
def get_crm_record(record_id: str):
    path = CRM_OUTPUTS_DIR / f"{record_id}.json"
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"CRM record '{record_id}' not found in {CRM_OUTPUTS_DIR}",
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {"id": record_id, "file": path.name, **data}
    except Exception as exc:
        logger.error("get_crm_record error for %s: %s", record_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))
