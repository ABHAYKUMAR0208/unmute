"""
validator.py
------------
Validates extracted CRM data before it gets pushed to HubSpot.

Ported as-is from the Personaplex project (src/extraction/validator.py) —
same service types, same required-field rules per type. This file has no
dependency on transcript schema, so nothing needed to change here.
"""

VALID_SERVICE_TYPES = {"taxi", "laundry", "food_order", "maintenance"}


def validate_taxi(data: dict) -> tuple[bool, list[str]]:
    errors = []
    for field in ["room_number", "destination", "pickup_time", "status"]:
        if not data.get(field):
            errors.append(f"Missing or empty: '{field}'")
    return len(errors) == 0, errors


def validate_laundry(data: dict) -> tuple[bool, list[str]]:
    errors = []
    for field in ["room_number", "status"]:
        if not data.get(field):
            errors.append(f"Missing or empty: '{field}'")
    if not isinstance(data.get("items"), list):
        errors.append("'items' must be a list")
    if data.get("urgency") not in {"urgent", "normal"}:
        errors.append("'urgency' must be urgent or normal")
    return len(errors) == 0, errors


def validate_food_order(data: dict) -> tuple[bool, list[str]]:
    errors = []
    for field in ["room_number", "status"]:
        if not data.get(field):
            errors.append(f"Missing or empty: '{field}'")
    if not isinstance(data.get("items"), list):
        errors.append("'items' must be a list")
    if data.get("urgency") not in {"urgent", "normal"}:
        errors.append("'urgency' must be urgent or normal")
    return len(errors) == 0, errors


def validate_maintenance(data: dict) -> tuple[bool, list[str]]:
    errors = []
    for field in ["room_number", "issue_description", "status"]:
        if not data.get(field):
            errors.append(f"Missing or empty: '{field}'")
    if data.get("urgency") not in {"urgent", "normal"}:
        errors.append("'urgency' must be urgent or normal")
    return len(errors) == 0, errors


_VALIDATORS = {
    "taxi": validate_taxi,
    "laundry": validate_laundry,
    "food_order": validate_food_order,
    "maintenance": validate_maintenance,
}


def validate(data: dict) -> tuple[bool, list[str]]:
    service_type = data.get("service_type")
    if service_type not in VALID_SERVICE_TYPES:
        return False, [f"Invalid service_type: '{service_type}'"]
    return _VALIDATORS[service_type](data)


def validate_all(services: list[dict]) -> list[tuple[dict, bool, list[str]]]:
    """
    Validates each service in a multi-service extraction independently.
    Returns one (service, is_valid, errors) tuple per service, so the
    caller can push whichever services are valid and skip/log whichever
    aren't — one malformed service (e.g. a taxi request missing a
    destination) shouldn't block a correctly-extracted food order in the
    same call from reaching HubSpot.
    """
    return [(service, *validate(service)) for service in services]
