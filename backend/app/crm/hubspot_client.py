"""
hubspot_client.py
------------------
All HubSpot I/O for the CRM worker: pushing service-request records,
pushing the transcript log, and pulling guest details by room number.

Merges Personaplex's src/crm/hubspot_connector.py (push side) and
src/crm/guest_lookup.py (pull side). Credentials/object-type IDs come
from Unmute's Settings object instead of raw os.environ.

push_transcript_log() reads the raw .jsonl directly (like Personaplex
did), so its role check is adapted to this project's real schema:
role values are "assistant"/"user", not Personaplex's "agent"/"guest".

guest_lookup functions (get_guest_by_room / get_phone_by_room) are ported
as utilities only — nothing in this project calls them yet.
"""

from __future__ import annotations

import json
import logging
import os

import requests

from ..config import settings

logger = logging.getLogger("crm.hubspot_client")

HUBSPOT_BASE_URL = "https://api.hubapi.com"


class HubSpotConfigError(EnvironmentError):
    """Raised when a required HubSpot credential/object-type is not configured."""


def get_headers() -> dict:
    if not settings.hubspot_access_token:
        raise HubSpotConfigError(
            "hubspot_access_token is not set. Add HUBSPOT_ACCESS_TOKEN to your .env.\n"
            "Get it from: HubSpot → Settings → Integrations → Private Apps."
        )
    return {
        "Authorization": f"Bearer {settings.hubspot_access_token}",
        "Content-Type": "application/json",
    }


# ── Object type resolution ──────────────────────────────────────────────

_OBJECT_TYPE_ATTR = {
    "taxi": "hubspot_taxi_object_type",
    "laundry": "hubspot_laundry_object_type",
    "food_order": "hubspot_food_object_type",
    "maintenance": "hubspot_maintenance_object_type",
    "payment": "hubspot_payment_object_type",
}


def get_object_type(service_type: str) -> str:
    attr = _OBJECT_TYPE_ATTR.get(service_type)
    if not attr:
        raise ValueError(f"Unknown service_type: '{service_type}'")
    value = getattr(settings, attr)
    if not value:
        raise HubSpotConfigError(f"{attr.upper()} is not set in .env")
    return value


# ── Payload builders (one per service type) ─────────────────────────────

def build_taxi_payload(data: dict) -> dict:
    return {"properties": {
        "room_number": data.get("room_number"),
        "destination": data.get("destination"),
        "pickup_time": data.get("pickup_time"),
        "status": data.get("status", "pending"),
    }}


def build_laundry_payload(data: dict) -> dict:
    return {"properties": {
        "room_number": data.get("room_number"),
        "items": json.dumps(data.get("items", [])),
        "pickup_time": data.get("pickup_time"),
        "delivery_deadline": data.get("delivery_deadline"),
        "special_notes": data.get("special_notes"),
        "urgency": data.get("urgency", "normal"),
        "status": data.get("status", "pending"),
    }}


def build_food_payload(data: dict) -> dict:
    return {"properties": {
        "room_number": data.get("room_number"),
        "items": json.dumps(data.get("items", [])),
        "delivery_deadline": data.get("delivery_deadline"),
        "special_notes": data.get("special_notes"),
        "urgency": data.get("urgency", "normal"),
        "status": data.get("status", "pending"),
    }}


def build_payment_payload(data: dict) -> dict:
    return {"properties": {
        "room_number": data.get("room_number"),
        "amount": data.get("amount"),
        "payment_method": data.get("payment_method"),
        "payment_status": data.get("payment_status"),
        "status": data.get("status", "pending"),
    }}


def build_maintenance_payload(data: dict) -> dict:
    return {"properties": {
        "room_number": data.get("room_number"),
        "issue_description": data.get("issue_description"),
        "urgency": data.get("urgency", "normal"),
        "pickup_time": data.get("pickup_time"),
        "status": data.get("status", "pending"),
    }}


PAYLOAD_BUILDERS = {
    "taxi": build_taxi_payload,
    "laundry": build_laundry_payload,
    "food_order": build_food_payload,
    "maintenance": build_maintenance_payload,
    "payment": build_payment_payload,
}


# ── Push: service-request record ────────────────────────────────────────

def push(data: dict) -> dict:
    """Creates a custom-object record in HubSpot for the given service request."""
    service_type = data.get("service_type")
    object_type = get_object_type(service_type)
    endpoint = f"{HUBSPOT_BASE_URL}/crm/v3/objects/{object_type}"
    payload = PAYLOAD_BUILDERS[service_type](data)

    response = requests.post(endpoint, headers=get_headers(), json=payload)
    if not response.ok:
        raise ConnectionError(
            f"HubSpot API returned {response.status_code}.\nResponse: {response.text}"
        )
    created_record = response.json()
    logger.info("%s record created. ID: %s", service_type, created_record.get("id"))
    return created_record


# ── Push: transcript log ────────────────────────────────────────────────

def push_transcript_log(data: dict, transcript_path: str) -> dict:
    """Logs the full conversation from a .jsonl transcript as its own HubSpot record."""
    with open(transcript_path, "r", encoding="utf-8") as f:
        lines = []
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            # This project's TranscriptWriter uses "assistant"/"user",
            # not Personaplex's "agent"/"guest".
            role = "Agent" if entry.get("role") == "assistant" else "Guest"
            lines.append(f"{role}: {entry.get('text', '')}")
        conversation_text = "\n".join(lines)

    if not settings.hubspot_transcript_object_type:
        raise HubSpotConfigError("hubspot_transcript_object_type is not set in .env")

    endpoint = f"{HUBSPOT_BASE_URL}/crm/v3/objects/{settings.hubspot_transcript_object_type}"
    payload = {
        "properties": {
            # Populated with the room value — see extractor.py docstring.
            "session_id": data.get("session_id"),
            "room_number": data.get("room_number"),
            "room_name": data.get("room_name"),
            "service_type": data.get("service_type"),
            "timestamp": data.get("timestamp"),
            "transcript_filename": os.path.basename(transcript_path),
            "status": "processed",
            "conversation": conversation_text,
        }
    }

    response = requests.post(endpoint, headers=get_headers(), json=payload)
    if not response.ok:
        raise ConnectionError(
            f"Transcript log push failed {response.status_code}: {response.text}"
        )
    created = response.json()
    logger.info("Transcript log created. ID: %s", created.get("id"))
    return created


# ── Pull: guest lookup by room number (ported utility, unused for now) ──

def get_guest_by_room(room_number: str) -> dict | None:
    if not settings.hubspot_guest_object_type:
        raise HubSpotConfigError(
            "hubspot_guest_object_type is not set in .env.\n"
            "Run the guest schema setup first (see --setup-guest)."
        )
    endpoint = f"{HUBSPOT_BASE_URL}/crm/v3/objects/{settings.hubspot_guest_object_type}/search"

    payload = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "room_number",
                "operator": "EQ",
                "value": str(room_number),
            }]
        }],
        "properties": ["room_number", "full_name", "phone", "email", "check_in", "check_out"],
        "limit": 1,
    }

    response = requests.post(endpoint, headers=get_headers(), json=payload)
    if not response.ok:
        raise ConnectionError(
            f"HubSpot search failed with {response.status_code}.\nResponse: {response.text}"
        )

    results = response.json().get("results", [])
    if not results:
        return None

    record = results[0]
    props = record.get("properties", {})
    return {
        "id": record.get("id"),
        "room_number": props.get("room_number"),
        "full_name": props.get("full_name"),
        "phone": props.get("phone"),
        "email": props.get("email"),
        "check_in": props.get("check_in"),
        "check_out": props.get("check_out"),
    }


def get_phone_by_room(room_number: str) -> str:
    guest = get_guest_by_room(room_number)
    if not guest:
        raise ValueError(f"No guest found for room {room_number}.")
    phone = guest.get("phone")
    if not phone:
        raise ValueError(f"Guest in room {room_number} has no phone number on record.")
    return phone


# ── One-time schema setup (run manually) ─────────────────────────────────

def _post_schema(schema: dict, attr_name: str) -> str:
    response = requests.post(f"{HUBSPOT_BASE_URL}/crm/v3/schemas", headers=get_headers(), json=schema)
    name = schema["name"]
    if response.status_code == 201:
        result = response.json()
        object_type = result.get("objectTypeId") or result.get("name")
        print(f"✓ '{name}' schema created.")
        print(f"  Add to .env: {attr_name.upper()}={object_type}")
        return object_type
    elif response.status_code == 409:
        print(f"✗ '{name}' schema already exists.")
        return ""
    else:
        raise ConnectionError(f"'{name}' failed {response.status_code}: {response.text}")


def create_taxi_schema() -> str:
    schema = {
        "name": "taxi_request",
        "labels": {"singular": "Taxi Request", "plural": "Taxi Requests"},
        "primaryDisplayProperty": "room_number",
        "properties": [
            {"name": "room_number", "label": "Room Number", "type": "string", "fieldType": "text"},
            {"name": "destination", "label": "Destination", "type": "string", "fieldType": "text"},
            {"name": "pickup_time", "label": "Pickup Time", "type": "string", "fieldType": "text"},
            {"name": "status", "label": "Status", "type": "string", "fieldType": "text"},
        ],
        "associatedObjects": [],
    }
    return _post_schema(schema, "hubspot_taxi_object_type")


def create_laundry_schema() -> str:
    schema = {
        "name": "laundry_request",
        "labels": {"singular": "Laundry Request", "plural": "Laundry Requests"},
        "primaryDisplayProperty": "room_number",
        "properties": [
            {"name": "room_number", "label": "Room Number", "type": "string", "fieldType": "text"},
            {"name": "items", "label": "Items", "type": "string", "fieldType": "text"},
            {"name": "pickup_time", "label": "Pickup Time", "type": "string", "fieldType": "text"},
            {"name": "delivery_deadline", "label": "Delivery Deadline", "type": "string", "fieldType": "text"},
            {"name": "special_notes", "label": "Special Notes", "type": "string", "fieldType": "text"},
            {"name": "urgency", "label": "Urgency", "type": "string", "fieldType": "text"},
            {"name": "status", "label": "Status", "type": "string", "fieldType": "text"},
        ],
        "associatedObjects": [],
    }
    return _post_schema(schema, "hubspot_laundry_object_type")


def create_food_schema() -> str:
    schema = {
        "name": "food_order",
        "labels": {"singular": "Food Order", "plural": "Food Orders"},
        "primaryDisplayProperty": "room_number",
        "properties": [
            {"name": "room_number", "label": "Room Number", "type": "string", "fieldType": "text"},
            {"name": "items", "label": "Items", "type": "string", "fieldType": "text"},
            {"name": "delivery_deadline", "label": "Delivery Deadline", "type": "string", "fieldType": "text"},
            {"name": "special_notes", "label": "Special Notes", "type": "string", "fieldType": "text"},
            {"name": "urgency", "label": "Urgency", "type": "string", "fieldType": "text"},
            {"name": "status", "label": "Status", "type": "string", "fieldType": "text"},
        ],
        "associatedObjects": [],
    }
    return _post_schema(schema, "hubspot_food_object_type")


def create_maintenance_schema() -> str:
    schema = {
        "name": "maintenance_request",
        "labels": {"singular": "Maintenance Request", "plural": "Maintenance Requests"},
        "primaryDisplayProperty": "room_number",
        "properties": [
            {"name": "room_number", "label": "Room Number", "type": "string", "fieldType": "text"},
            {"name": "issue_description", "label": "Issue Description", "type": "string", "fieldType": "text"},
            {"name": "urgency", "label": "Urgency", "type": "string", "fieldType": "text"},
            {"name": "pickup_time", "label": "Pickup Time", "type": "string", "fieldType": "text"},
            {"name": "status", "label": "Status", "type": "string", "fieldType": "text"},
        ],
        "associatedObjects": [],
    }
    return _post_schema(schema, "hubspot_maintenance_object_type")


def create_payment_schema() -> str:
    schema = {
        "name": "payment_request",
        "labels": {"singular": "Payment Request", "plural": "Payment Requests"},
        "primaryDisplayProperty": "room_number",
        "properties": [
            {"name": "room_number", "label": "Room Number", "type": "string", "fieldType": "text"},
            {"name": "amount", "label": "Amount", "type": "string", "fieldType": "text"},
            {"name": "payment_method", "label": "Payment Method", "type": "string", "fieldType": "text"},
            {"name": "payment_status", "label": "Payment Status", "type": "string", "fieldType": "text"},
            {"name": "status", "label": "Status", "type": "string", "fieldType": "text"},
        ],
        "associatedObjects": [],
    }
    return _post_schema(schema, "hubspot_payment_object_type")


def create_transcript_schema() -> str:
    schema = {
        "name": "transcript_log",
        "labels": {"singular": "Transcript Log", "plural": "Transcript Logs"},
        "primaryDisplayProperty": "session_id",
        "properties": [
            {"name": "session_id", "label": "Session ID", "type": "string", "fieldType": "text"},
            {"name": "room_number", "label": "Room Number", "type": "string", "fieldType": "text"},
            {"name": "room_name", "label": "Room Name", "type": "string", "fieldType": "text"},
            {"name": "conversation", "label": "Conversation", "type": "string", "fieldType": "textarea"},
            {"name": "service_type", "label": "Service Type", "type": "string", "fieldType": "text"},
            {"name": "timestamp", "label": "Timestamp", "type": "string", "fieldType": "text"},
            {"name": "transcript_filename", "label": "Transcript Filename", "type": "string", "fieldType": "text"},
            {"name": "status", "label": "Status", "type": "string", "fieldType": "text"},
        ],
        "associatedObjects": [],
    }
    return _post_schema(schema, "hubspot_transcript_object_type")


def create_guest_schema() -> str:
    schema = {
        "name": "guest",
        "labels": {"singular": "Guest", "plural": "Guests"},
        "primaryDisplayProperty": "full_name",
        "properties": [
            {"name": "room_number", "label": "Room Number", "type": "string", "fieldType": "text"},
            {"name": "full_name", "label": "Full Name", "type": "string", "fieldType": "text"},
            {"name": "phone", "label": "Phone", "type": "string", "fieldType": "text"},
            {"name": "email", "label": "Email", "type": "string", "fieldType": "text"},
            {"name": "check_in", "label": "Check In", "type": "string", "fieldType": "text"},
            {"name": "check_out", "label": "Check Out", "type": "string", "fieldType": "text"},
        ],
        "associatedObjects": [],
    }
    return _post_schema(schema, "hubspot_guest_object_type")


if __name__ == "__main__":
    import sys

    _SETUP_COMMANDS = {
        "--setup-taxi": create_taxi_schema,
        "--setup-laundry": create_laundry_schema,
        "--setup-food": create_food_schema,
        "--setup-maintenance": create_maintenance_schema,
        "--setup-payment": create_payment_schema,
        "--setup-transcript": create_transcript_schema,
        "--setup-guest": create_guest_schema,
    }
    for flag, fn in _SETUP_COMMANDS.items():
        if flag in sys.argv:
            fn()
