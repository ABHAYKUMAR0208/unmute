"""
extractor.py
------------
Reads a hotel call transcript (.jsonl, one turn per line) and uses a local
LLM (Phi-3 Mini via Ollama) to extract structured service-request JSON —
one object per distinct service the guest requested in the call.

Originally ported from Personaplex's src/extraction/extractor.py
("Pipeline B"). Multi-service extraction (a transcript can produce more
than one service request — e.g. food + taxi in one call) is ported from
a later Personaplex revision that rewrote extraction to return a JSON
array instead of a single object. Two things were deliberately NOT
carried over from that version:

  - It disabled Ollama's format=json mode in favor of regex-extracting a
    JSON array from free-form output. We keep format=json — arrays are
    valid top-level JSON, no reason to give up the stricter guarantee.
  - It built its own hardcoded MENU price dicts and pushed a separate
    combined "payment" HubSpot record. Unmute already has a real billing
    pipeline (app/payments/billing_service.py) with its own catalog and
    PayU integration, called once per validated service from
    app/crm/worker.py — so pricing has one source of truth instead of two.

Determinism (temperature=0, fixed seed) and the multi-item few-shot
example were added separately to fix small-model unreliability on
multi-item extraction (see git history) — both are kept here.

Transcript line shape (this project's TranscriptWriter format):
    {"room": "...", "role": "assistant"|"user", "text": "...", "ts": 1785480387.75}
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import requests
import re

from ..config import settings

logger = logging.getLogger("crm.extractor")

SYSTEM_PROMPT = """You are a hotel operations assistant. Read the call transcript and extract ALL service requests the guest made into a JSON array — one object per DISTINCT service.

Always return ONLY a valid JSON array — no explanation, no markdown, no code fences.
Even if there is only one service requested, still return an array with exactly one object in it. Never return a single bare object.
IMPORTANT: Always include ALL fields for each object, even if the value is "pending" or "normal". Never omit any field.

For EACH service, first identify its service_type from: taxi, laundry, food_order, maintenance

Then build that service's object using the matching structure:

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

IMPORTANT: Always include ALL fields in every object, even if the value is "pending" or "normal". Never omit any field.

Always set status to "pending".
urgency is "urgent" if guest expressed urgency or discomfort, otherwise "normal".

CRITICAL — multiple distinct services: if the guest asked for more than one
kind of service in the same call (e.g. food AND a taxi), the array must
contain one object per DISTINCT service, each following its own schema
above. Never merge two different services into one object.

CRITICAL — multiple items within one service: for laundry/food_order, the
"items" array must contain ONE ENTRY PER DISTINCT ITEM mentioned, each
with its own correct quantity. Never collapse multiple items into one
entry, and never drop items after the first one.

Example — transcript:
  Guest: I'd like to order 2 burgers and 3 pizzas to room 305.
  Agent: Got it, 2 burgers and 3 pizzas to room 305. Anything else?
  Guest: Yes, also book me a taxi to the airport for 6pm.
  Agent: Sure, taxi to the airport at 6pm for room 305. Anything else?
  Guest: No that's all.

Correct extraction (note: TWO objects — one food_order with TWO item
entries, one taxi — not merged, nothing dropped):
[
  {
    "service_type": "food_order",
    "room_number": "305",
    "items": [
      {"name": "burger", "quantity": 2},
      {"name": "pizza", "quantity": 3}
    ],
    "delivery_deadline": null,
    "special_notes": null,
    "urgency": "normal",
    "status": "pending"
  },
  {
    "service_type": "taxi",
    "room_number": "305",
    "destination": "airport",
    "pickup_time": "6pm",
    "status": "pending"
  }
]

WRONG (do not do this — missing the taxi service entirely):
[{"service_type": "food_order", "room_number": "305", "items": [{"name": "burger", "quantity": 2}, {"name": "pizza", "quantity": 3}], ...}]

WRONG (do not do this — services merged into one object):
[{"service_type": "food_order", "room_number": "305", "items": [...], "destination": "airport", "pickup_time": "6pm", ...}]

WRONG (do not do this — bare object instead of an array):
{"service_type": "taxi", "room_number": "305", ...}
 
Example — a transcript with only ONE service still gets wrapped in an array:
  Guest: I'd like 2 towels sent up to room 412, please.
  Agent: Sure, 2 towels to room 412 right away.
 
Correct extraction (note: still an array, with exactly one object in it):
[
  {
    "service_type": "laundry",
    "room_number": "412",
    "items": [{"name": "towel", "quantity": 2}],
    "pickup_time": null,
    "delivery_deadline": null,
    "special_notes": null,
    "urgency": "normal",
    "status": "pending"
  }
]
 
WRONG for the single-service case too (never drop the array just because there's one item):
{"service_type": "laundry", "room_number": "412", "items": [{"name": "towel", "quantity": 2}], ...}
"""


def parse_jsonl_transcript(raw: str) -> tuple[str, dict]:
    """
    Turns raw .jsonl content (this project's TranscriptWriter format) into
    a plain-text transcript + call metadata shared by every service
    extracted from it.
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


def extract(transcript: str, metadata: dict | None = None) -> list[dict]:
    """
    Sends transcript to Phi-3 Mini via Ollama, returns a list of
    structured service-request dicts (one per distinct service).
    """
    payload = {
        "model": "qwen2.5:14b",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
        "stream": False,
        # "format": "json",  # forces Ollama to return syntactically valid JSON
        "options": {
            "temperature": 0,   # deterministic — this is extraction, not creative generation
            "seed": 42,         # same input -> same output, every run
            "top_p": 1.0,
        },
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
 
    # Without format=json's grammar constraint, the model may wrap its
    # answer in prose despite instructions not to. Prefer an array match
    # (the documented correct shape); fall back to a bare object.
    match = re.search(r"\[.*\]", raw_response, re.DOTALL)
    if match:
        parsed = json.loads(match.group(0))
    else:
        match = re.search(r"\{.*\}", raw_response, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON found in response: {raw_response}")
        parsed = json.loads(match.group(0))

    # Defensive: despite explicit instructions, a small model can still
    # occasionally return a bare object instead of a one-item array.
    # Normalize rather than crash the whole transcript over this.
    if isinstance(parsed, dict):
        logger.warning(
            "Model returned a single object instead of an array — wrapping it. "
            "This shouldn't normally happen; worth a look if it's frequent."
        )
        services = [parsed]
    elif isinstance(parsed, list):
        services = parsed
    else:
        raise ValueError(f"Unexpected extraction result type: {type(parsed)}")

    for service in services:
        # Defaults for fields Phi-3 Mini sometimes omits
        service.setdefault("status", "pending")
        service.setdefault("urgency", "normal")

        if metadata:
            service["session_id"] = metadata.get("session_id")  # = room value
            service["room_name"] = metadata.get("room")
            service["timestamp"] = metadata.get("timestamp")

    return services


def extract_from_file(filepath: str) -> list[dict]:
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
