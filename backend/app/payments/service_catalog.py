"""
service_catalog.py — Example hotel service menu/catalog.

This is sample data so the package runs out of the box. In a real
deployment you'd likely replace `get_catalog`/`lookup_price` with a call
into your own menu/PMS system — the rest of the worker doesn't depend on
this file at all (callers pass unit_price explicitly in ServiceRequest).
"""

from __future__ import annotations

from .models import ServiceType

FOOD_MENU = {
    # ── Your actual menu ──────────────────────────────────────────────────
    "cheese pizza": 349.0,
    "burger": 199.0,
    "sandwich": 149.0,
    "cold coffee": 149.0,

    # ── Indian ────────────────────────────────────────────────────────────
    "butter chicken": 450.0,
    "paneer tikka": 350.0,
    "dal makhani": 280.0,
    "biryani": 380.0,
    "naan": 60.0,
    "roti": 40.0,
    "rice": 120.0,
    "lemon rice": 160.0,
    "manchurian": 220.0,  # generic alias — guests rarely say "veg/gobi manchurian" explicitly
    "veg manchurian": 220.0,
    "gobi manchurian": 220.0,
    "chicken manchurian": 260.0,
    "raita": 80.0,
    "french fries": 200.0,

    # ── Starters ──────────────────────────────────────────────────────────
    "soup": 180.0,
    "salad": 220.0,

    # ── Beverages ─────────────────────────────────────────────────────────
    "coke": 80.0,
    "pepsi": 80.0,
    "water bottle": 40.0,
    "fresh juice": 150.0,
    "tea": 60.0,
    "coffee": 100.0,
    "beer": 350.0,

    # ── Desserts ─────────────────────────────────────────────────────────
    "gulab jamun": 120.0,
    "ice cream": 180.0,
    "brownie": 200.0,
}

ROOM_SERVICES = {
    "basic cleaning": 200.0,
    "deep cleaning": 500.0,
    "towel replacement": 0.0,
    "minibar refill": 300.0,
    "extra pillow": 0.0,
    "extra blanket": 0.0,
    "bed making": 100.0,
}

CAB_SERVICES = {
    "airport pickup": 1200.0,
    "airport drop": 1200.0,
    "local 4hr": 800.0,
    "local 8hr": 1500.0,
    "outstation per km": 15.0,
    "railway station": 600.0,
}

RESTAURANT_SERVICES = {
    "table reservation": 0.0,
    "private dining": 2000.0,
    "birthday decoration": 1500.0,
    "anniversary decoration": 2000.0,
    "cake 1kg": 800.0,
}

LAUNDRY_SERVICES = {
    "shirt wash": 80.0,
    "trouser wash": 100.0,
    "suit dry clean": 400.0,
    "saree dry clean": 350.0,
    "express service": 200.0,
}

SPA_SERVICES = {
    "swedish massage 60min": 2500.0,
    "thai massage 60min": 2800.0,
    "facial": 1500.0,
    "manicure": 800.0,
    "pedicure": 800.0,
}


def get_catalog(service_type: ServiceType) -> dict[str, float]:
    catalogs = {
        ServiceType.FOOD_ORDER: FOOD_MENU,
        ServiceType.ROOM_CLEANING: ROOM_SERVICES,
        ServiceType.CAB_BOOKING: CAB_SERVICES,
        ServiceType.RESTAURANT_BOOKING: RESTAURANT_SERVICES,
        ServiceType.LAUNDRY: LAUNDRY_SERVICES,
        ServiceType.SPA: SPA_SERVICES,
    }
    return catalogs.get(service_type, {})


def lookup_price(service_type: ServiceType, item_name: str) -> float | None:
    catalog = get_catalog(service_type)
    item_lower = item_name.lower().strip()

    if item_lower in catalog:
        return catalog[item_lower]

    for name, price in catalog.items():
        if item_lower in name or name in item_lower:
            return price

    return None
