"""
service_catalog.py — Hotel service menu/catalog.

Sample data so the package runs out of the box. In a real deployment
you'd likely replace `get_catalog`/`lookup_price` with a call into your
own menu/PMS system — the rest of the worker doesn't depend on this file
at all (callers pass unit_price explicitly in ServiceRequest).

IMPORTANT — naming convention, read before adding items:
Catalog keys are matched as case-insensitive SUBSTRINGS against what the
guest said (see payments/payment_bridge.py's _extract_items and
billing_service.py's per-item lookup_price). This means:

  - Prefer full, specific dish names ("chicken biryani", "veg manchurian")
    over bare generic words ("chicken", "veg") as standalone keys. A bare
    "chicken" key would match INSIDE "chicken biryani", "chicken tikka",
    etc. and can cause duplicate/overlapping items on a single dish.
  - Only add a short/generic key (like the existing "manchurian" alias)
    when you've deliberately decided guests say it bare often enough to
    be worth the small risk of it firing for compound dishes too — that
    tradeoff was made deliberately for "manchurian", not by default.
  - Longer, more specific names are checked before shorter ones
    (get_catalog callers sort by len(name), descending), so a specific
    dish is preferred over a generic alias when both could match — but
    this only helps if the generic alias doesn't also fire in addition.
"""

from __future__ import annotations

from .models import ServiceType

FOOD_MENU = {
    # ── House specials ───────────────────────────────────────────────────
    "cheese pizza": 349.0,
    "margherita pizza": 329.0,
    "pepperoni pizza": 399.0,
    "burger": 199.0,
    "chicken burger": 249.0,
    "veg burger": 189.0,
    "sandwich": 149.0,
    "club sandwich": 199.0,
    "grilled sandwich": 169.0,
    "cold coffee": 149.0,   

    # ── Indian — starters ────────────────────────────────────────────────
    "paneer tikka": 350.0,
    "chicken tikka": 380.0,
    "malai tikka": 400.0,
    "seekh kebab": 380.0,
    "hara bhara kebab": 280.0,
    "chicken 65": 320.0,
    "amritsari fish": 400.0,
    "papdi chaat": 150.0,
    "samosa": 80.0,
    "pakora": 120.0,

    # ── Indian — mains ───────────────────────────────────────────────────
    "butter chicken": 450.0,
    "chicken tikka masala": 460.0,
    "dal makhani": 280.0,
    "dal tadka": 220.0,
    "paneer butter masala": 340.0,
    "palak paneer": 320.0,
    "kadai paneer": 340.0,
    "shahi paneer": 350.0,
    "malai kofta": 330.0,
    "chana masala": 240.0,
    "rajma": 230.0,
    "mixed vegetable curry": 260.0,
    "egg curry": 260.0,
    "mutton curry": 480.0,
    "fish curry": 460.0,
    "prawn curry": 500.0,

    # ── Indian — rice & biryani ──────────────────────────────────────────
    "chicken biryani": 380.0,
    "mutton biryani": 450.0,
    "veg biryani": 320.0,
    "egg biryani": 300.0,
    "hyderabadi biryani": 420.0,
    "jeera rice": 180.0,
    "lemon rice": 160.0,
    "curd rice": 150.0,
    "rice": 120.0,
    "pulao": 220.0,

    # ── Indian — chinese-indian ──────────────────────────────────────────
    "manchurian": 220.0,  # generic alias — guests rarely say "veg/gobi manchurian" explicitly
    "veg manchurian": 220.0,
    "gobi manchurian": 220.0,
    "chicken manchurian": 260.0,
    "chilli paneer": 260.0,
    "chilli chicken": 280.0,

    # ── Indian — breads ──────────────────────────────────────────────────
    "naan": 60.0,
    "butter naan": 70.0,
    "garlic naan": 80.0,
    "roti": 40.0,
    "butter roti": 50.0,
    "tandoori roti": 45.0,
    "paratha": 60.0,
    "aloo paratha": 90.0,
    "kulcha": 60.0,
    "bhatura": 60.0,

    # ── Indian — accompaniments ──────────────────────────────────────────
    "raita": 80.0,
    "papad": 40.0,
    "pickle": 30.0,
    "salad": 220.0,

    # ── Chinese ───────────────────────────────────────────────────────────
    "veg fried rice": 220.0,
    "chicken fried rice": 260.0,
    "egg fried rice": 240.0,
    "schezwan fried rice": 260.0,
    "hakka noodles": 220.0,
    "chicken noodles": 260.0,
    "schezwan noodles": 260.0,
    "spring rolls": 200.0,
    "chicken lollipop": 320.0,
    "sweet corn soup": 160.0,
    "hot and sour soup": 170.0,
    "manchow soup": 170.0,
    "wonton soup": 190.0,
    "dim sum": 280.0,
    "kung pao chicken": 340.0,

    # ── Mexican ───────────────────────────────────────────────────────────
    "chicken tacos": 320.0,
    "veg tacos": 280.0,
    "chicken burrito": 340.0,
    "veg burrito": 300.0,
    "nachos": 280.0,
    "chicken quesadilla": 320.0,
    "veg quesadilla": 280.0,
    "guacamole": 200.0,
    "fajita": 350.0,
    "enchiladas": 320.0,

    # ── Continental / Italian ─────────────────────────────────────────────
    "pasta alfredo": 320.0,
    "pasta arrabbiata": 300.0,
    "spaghetti bolognese": 340.0,
    "penne pasta": 300.0,
    "lasagna": 380.0,
    "risotto": 360.0,
    "grilled chicken": 380.0,
    "grilled fish": 420.0,
    "caesar salad": 260.0,
    "greek salad": 240.0,
    "bruschetta": 220.0,
    "garlic bread": 150.0,
    "mushroom soup": 180.0,
    "tomato soup": 160.0,

    # ── Starters (general) ───────────────────────────────────────────────
    "soup": 180.0,
    "french fries": 200.0,
    "onion rings": 180.0,

    # ── Beverages — soft drinks & water ──────────────────────────────────
    "coke": 80.0,
    "pepsi": 80.0,
    "sprite": 80.0,
    "soda": 60.0,
    "water bottle": 40.0,

    # ── Beverages — juices & shakes ───────────────────────────────────────
    "fresh juice": 150.0,
    "orange juice": 150.0,
    "watermelon juice": 130.0,
    "mango shake": 180.0,
    "chocolate shake": 190.0,
    "vanilla shake": 180.0,
    "lassi": 120.0,
    "buttermilk": 60.0,
    "mocktail": 220.0,

    # ── Beverages — hot ───────────────────────────────────────────────────
    "tea": 60.0,
    "masala chai": 70.0,
    "green tea": 80.0,
    "coffee": 100.0,
    "cappuccino": 150.0,
    "latte": 160.0,
    "espresso": 140.0,
    "hot chocolate": 170.0,

    # ── Beverages — alcoholic ─────────────────────────────────────────────
    "beer": 350.0,
    "wine glass": 500.0,
    "whiskey peg": 450.0,
    "vodka peg": 400.0,
    "rum peg": 380.0,
    "cocktail": 450.0,

    # ── Desserts ─────────────────────────────────────────────────────────
    "gulab jamun": 120.0,
    "rasmalai": 150.0,
    "jalebi": 100.0,
    "kheer": 130.0,
    "ice cream": 180.0,
    "brownie": 200.0,
    "chocolate cake": 250.0,
    "cheesecake": 280.0,
    "tiramisu": 300.0,
    "fruit salad": 150.0,
    "pastry": 180.0,
}

ROOM_SERVICES = {
    "basic cleaning": 200.0,
    "deep cleaning": 500.0,
    "turndown service": 0.0,
    "towel replacement": 0.0,
    "bedsheet change": 0.0,
    "minibar refill": 300.0,
    "extra pillow": 0.0,
    "extra blanket": 0.0,
    "extra towel": 0.0,
    "bed making": 100.0,
    "room fragrance service": 150.0,
    "iron and ironing board": 0.0,
}

CAB_SERVICES = {
    "airport pickup": 1200.0,
    "airport drop": 1200.0,
    "local 4hr": 800.0,
    "local 8hr": 1500.0,
    "outstation per km": 15.0,
    "railway station": 600.0,
    "bus station transfer": 500.0,
    "city tour half day": 1800.0,
    "city tour full day": 3200.0,
}

RESTAURANT_SERVICES = {
    "table reservation": 0.0,
    "private dining": 2000.0,
    "rooftop dining": 2500.0,
    "candlelight dinner setup": 3000.0,
    "birthday decoration": 1500.0,
    "anniversary decoration": 2000.0,
    "cake 1kg": 800.0,
    "cake half kg": 450.0,
    "live bbq setup": 3500.0,
    "buffet per person": 900.0,
}

LAUNDRY_SERVICES = {
    "shirt wash": 80.0,
    "trouser wash": 100.0,
    "suit dry clean": 400.0,
    "saree dry clean": 350.0,
    "kurta dry clean": 250.0,
    "jacket dry clean": 350.0,
    "blanket dry clean": 500.0,
    "express service": 200.0,
    "same day laundry": 300.0,
    "ironing per item": 40.0,
}

SPA_SERVICES = {
    "swedish massage 60min": 2500.0,
    "thai massage 60min": 2800.0,
    "deep tissue massage 60min": 3000.0,
    "aromatherapy massage 60min": 2700.0,
    "hot stone massage 60min": 3200.0,
    "couples massage 60min": 5000.0,
    "facial": 1500.0,
    "gold facial": 2200.0,
    "manicure": 800.0,
    "pedicure": 800.0,
    "mani pedi combo": 1400.0,
    "steam bath": 500.0,
    "sauna session": 500.0,
    "hair spa": 1800.0,
}

GYM_POOL_SERVICES = {
    "personal training session": 1000.0,
    "yoga session": 700.0,
    "pool towel rental": 100.0,
    "swimming lesson": 1200.0,
    "poolside cabana": 1500.0,
}

BUSINESS_SERVICES = {
    "meeting room per hour": 2000.0,
    "conference hall half day": 15000.0,
    "conference hall full day": 25000.0,
    "printing per page": 10.0,
    "scanning per page": 10.0,
    "projector rental": 1500.0,
    "video conferencing setup": 2500.0,
}

CONCIERGE_SERVICES = {
    "luggage storage": 0.0,
    "wake up call": 0.0,
    "newspaper delivery": 0.0,
    "sightseeing package half day": 2000.0,
    "sightseeing package full day": 3500.0,
    "event ticket booking assistance": 0.0,
    "courier service": 250.0,
    "flower bouquet delivery": 800.0,
    "gift wrapping": 100.0,
}

KIDS_PET_SERVICES = {
    "babysitting per hour": 400.0,
    "kids play area access": 300.0,
    "pet sitting per hour": 350.0,
    "pet food service": 250.0,
}

# ── Food add-ons / special-instruction extras ────────────────────────────
# These are what guests say when Kelly asks "any special instructions?" —
# billed as their own extra line item alongside whatever dish they modify,
# not folded into the dish's price (keeps pricing transparent, and matches
# how the current substring-based extraction already works: each catalog
# key becomes its own BillItem regardless of which dish it was said with).
ADD_ON_SERVICES = {
    "extra cheese": 40.0,
    "extra butter": 30.0,
    "extra sweetness": 0.0,
    "extra sugar": 0.0,
    "extra spicy": 0.0,
    "extra mayo": 20.0,
    "extra sauce": 20.0,
    "extra chutney": 20.0,
    "extra masala": 20.0,
    "extra ghee": 30.0,
    "extra chocolate": 40.0,
    "extra cream": 30.0,
    "extra toppings": 50.0,
    "extra paneer": 60.0,
    "extra chicken": 80.0,
    "extra ice": 0.0,
    "extra shot": 40.0,  # coffee add-on: an extra espresso shot
    "less spicy": 0.0,
    "no onion": 0.0,
    "no garlic": 0.0,
    "gluten free bread": 30.0,
}


ADDONS = {
    # ── Cheese / dairy ───────────────────────────────────────────────────
    "extra cheese": 40.0,
    "extra butter": 20.0,
    "extra paneer": 60.0,
    "extra cream": 30.0,

    # ── Protein ──────────────────────────────────────────────────────────
    "extra chicken": 80.0,
    "extra egg": 20.0,
    "extra prawn": 100.0,

    # ── Sauce / gravy / spice level ──────────────────────────────────────
    "extra sauce": 20.0,
    "extra gravy": 30.0,
    "extra masala": 30.0,
    "extra mayo": 20.0,
    "extra ketchup": 0.0,
    "extra spicy": 0.0,
    "extra mild": 0.0,
    "less spicy": 0.0,
    "no spice": 0.0,
    "no onion": 0.0,
    "no garlic": 0.0,

    # ── Sweetness ────────────────────────────────────────────────────────
    "extra sweet": 0.0,
    "extra sweetness": 0.0,
    "extra sugar": 0.0,
    "no sugar": 0.0,
    "less sweet": 0.0,

    # ── Veggies / misc ───────────────────────────────────────────────────
    "extra veggies": 30.0,
    "extra vegetables": 30.0,
    "extra ice": 0.0,
    "extra shot": 40.0,  # e.g. an extra espresso shot in coffee
}


def parse_item_with_addons(raw_name: str) -> tuple[str, list[tuple[str, float]]]:
    """
    Splits a guest-spoken item name into (base_dish_text, [(addon_name, addon_price), ...]).

    Guests describe add-ons inline with the dish rather than as separate
    catalog items — "pasta with extra cheese", "biryani, extra spicy,
    extra butter" — so this strips every recognized ADDONS phrase out of
    the text (longest phrases first, so "extra sweetness" doesn't get
    partially eaten by a shorter unrelated match), leaving just the base
    dish name for the normal catalog lookup_price() substring match.

    Connector words left behind ("with", "and", stray commas) are cleaned
    up so the remaining base text matches cleanly.
    """
    text = raw_name.lower()
    found_addons: list[tuple[str, float]] = []

    for addon_name in sorted(ADDONS, key=len, reverse=True):
        if addon_name in text:
            found_addons.append((addon_name, ADDONS[addon_name]))
            text = text.replace(addon_name, " ")

    # Clean up leftover connector words / punctuation from removed addons.
    for connector in (" with ", " and ", ","):
        text = text.replace(connector, " ")
    base = " ".join(text.split()).strip()

    return base, found_addons


def lookup_price_with_addons(service_type: ServiceType, raw_name: str) -> tuple[str, float] | None:
    """
    Resolves a guest-spoken item name (possibly with inline add-ons) to a
    (display_name, total_unit_price) pair, or None if the base dish can't
    be matched in the catalog at all.

    Use this instead of calling lookup_price() directly when the name may
    contain add-on phrasing — e.g. from billing_service.py's per-item loop.
    """
    base, addons = parse_item_with_addons(raw_name)

    base_price = lookup_price(service_type, base) if base else None
    if base_price is None:
        # Add-ons might have been recognized, but without a matched base
        # dish we don't guess a price for it — report failure rather than
        # billing a partial/wrong item.
        return None

    addon_total = sum(price for _, price in addons)
    if addons:
        display_name = base + " + " + ", ".join(name for name, _ in addons)
    else:
        display_name = base
    return display_name, base_price + addon_total


def get_catalog(service_type: ServiceType) -> dict[str, float]:
    catalogs = {
        ServiceType.FOOD_ORDER: {**FOOD_MENU, **ADD_ON_SERVICES},
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