"""
maintenance.py — Background sweep that expires stale pending bills.

Without this, a bill that's created but never paid (guest changed their
mind, network hiccup, abandoned checkout) stays 'pending' forever and
keeps showing up in /api/unpaid-bills totals.
"""

from __future__ import annotations

import asyncio
import logging

from .bill_generator import BillGenerator

logger = logging.getLogger("payu_worker.maintenance")


async def run_expiry_sweep_forever(bill_generator: BillGenerator, interval_seconds: int = 300):
    """Run `expire_stale_pending_bills` every `interval_seconds` until cancelled."""
    while True:
        try:
            await asyncio.to_thread(bill_generator.expire_stale_pending_bills)
        except Exception:
            # A failed sweep should never take the app down.
            logger.exception("Expiry sweep failed — will retry next interval")
        await asyncio.sleep(interval_seconds)
