"""
extractor.py
------------
Reads a hotel call transcript (.jsonl, one turn per line) and uses a local
LLM (Phi-3 Mini via Ollama) to extract a structured service-request JSON.

Ported from Personaplex's src/extraction/extractor.py ("Pipeline B" — the
pipeline that actually feeds HubSpot). Extraction logic/prompt is
unchanged; the transcript-parsing layer was rewritten to match this
project's actual TranscriptWriter output format, which differs from
Personaplex's:

    Personaplex line:  {"session_id": ..., "room": ..., "role": "agent"|"guest", "text": ...}
    This project's line: {"room": ...,               "role": "assistant"|"user", "text": ..., "ts": <unix float>}

Notably there is no session_id field here — TranscriptWriter identifies a
call purely by `room` (already a fresh uuid4-derived name minted per
session in main.py's /token endpoint, so it plays the same "unique per
call" role session_id played in Personaplex). Per product decision, we
still populate a `session_id` field on the extracted record so downstream
HubSpot properties/dashboard keep that name — its value is just the room
name.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import requests

from ..config import settings

logger = logging.getLogger("crm.extractor")

SYSTEM_PROMPT = """You are a hotel operations assistant. Read the call transcript and extract the service request into a structured JSON object.

Always return ONLY a valid JSON object — no explanation, no markdown, no code fences.
IMPORTANT: Always include ALL fields in your response, even if the value is "pending" or "normal". Never omit any field.

First identify the service_type from: taxi, laundry, food_order, maintenance

Then return the matching structure:

If taxi:
{
  "service_type": "taxi",
  "room_number": "string or null",
  "destination": "string or null",
  "pickup_time": "string or null",
  "status": "pending"
}

If laundry:
{
  "service_type": "laundry",
  "room_number": "string or null",
  "items": [{"name": "string", "quantity": integer}],
  "pickup_time": "string or null",
  "delivery_deadline": "string or null",
  "special_notes": "string or null",
  "urgency": "urgent | normal",
  "status": "pending"
}

If food_order:
{
  "service_type": "food_order",
  "room_number": "string or null",
  "items": [{"name": "string", "quantity": integer}],
  "delivery_deadline": "string or null",
  "special_notes": "string or null",
  "urgency": "urgent | normal",
  "status": "pending"
}

If maintenance:
{
  "service_type": "maintenance",
  "room_number": "string or null",
  "issue_description": "string or null",
  "urgency": "urgent | normal",
  "pickup_time": "string or null",
  "status": "pending"
}

IMPORTANT: Always include ALL fields in your response, even if the value is "pending" or "normal". Never omit any field.

Always set status to "pending".
urgency is "urgent" if guest expressed urgency or discomfort, otherwise "normal".
"""


def parse_jsonl_transcript(raw: str) -> tuple[str, dict]:
    """
    Turns raw .jsonl content (this project's TranscriptWriter format) into
    a plain-text transcript + call metadata.

    Real line shape: {"room": "...", "role": "assistant"|"user", "text": "...", "ts": 1785480387.75}
    """
    lines = []
    room_name: str | None = None
    last_ts: float | None = None

    for line in raw.strip().split("\n"):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        if room_name is None:
            room_name = entry.get("room")

        ts = entry.get("ts")
        if isinstance(ts, (int, float)):
            last_ts = ts

        role = "Agent" if entry.get("role") == "assistant" else "Guest"
        lines.append(f"{role}: {entry.get('text', '')}")

    timestamp_iso = (
        datetime.fromtimestamp(last_ts, tz=timezone.utc).isoformat()
        if last_ts is not None
        else None
    )

    metadata = {
        # session_id kept for HubSpot/dashboard continuity — populated with
        # the room value, since this project has no separate session_id.
        "session_id": room_name,
        "room": room_name,
        "timestamp": timestamp_iso,
    }
    return "\n".join(lines), metadata


def extract(transcript: str, metadata: dict | None = None) -> dict:
    """Sends transcript to Phi-3 Mini via Ollama, returns structured dict."""
    payload = {
        "model": "phi3:mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
        "stream": False,
        "format": "json",  # forces Ollama to return valid JSON
    }

    logger.debug("Calling Ollama at %s", settings.ollama_url)
    response = requests.post(settings.ollama_url, json=payload)

    if not response.ok:
        raise ConnectionError(f"Ollama API {response.status_code}: {response.text}")

    raw_response = response.json()["message"]["content"].strip()

    # Strip markdown fences if present
    if raw_response.startswith("```"):
        raw_response = raw_response.strip("`")
        if raw_response.startswith("json"):
            raw_response = raw_response[4:]
        raw_response = raw_response.strip()

    extracted = json.loads(raw_response)

    # Defaults for fields Phi-3 Mini sometimes omits
    extracted.setdefault("status", "pending")
    extracted.setdefault("urgency", "normal")

    if metadata:
        extracted["session_id"] = metadata.get("session_id")  # = room value
        extracted["room_name"] = metadata.get("room")
        extracted["timestamp"] = metadata.get("timestamp")

    return extracted


def extract_from_file(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    first_line = raw.strip().split("\n")[0].strip()
    if first_line.startswith("{"):
        transcript, metadata = parse_jsonl_transcript(raw)
    else:
        transcript, metadata = raw, {}

    if not transcript.strip():
        raise ValueError(f"No usable transcript content in file: {filepath}")

    return extract(transcript, metadata)
