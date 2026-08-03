"""
config.py — Settings for the PayU worker.

Design goals:
  * Never crash on import. A missing/misconfigured env var should surface
    as a clear, single error message when the worker actually starts
    (via `settings.validate()`), not as a random ImportError/ValueError
    somewhere deep in the call stack.
  * Everything is overridable via environment variables so the same
    package can be dropped into any project / container.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _env_list(name: str, default: list[str]) -> list[str]:
    val = os.getenv(name)
    if not val:
        return default
    return [v.strip() for v in val.split(",") if v.strip()]


@dataclass
class PayuWorkerSettings:
    """
    All configuration for the worker. Instantiate with no args to read
    from the environment (via python-dotenv), or override fields directly
    for tests / multi-tenant setups:

        settings = PayuWorkerSettings(hotel_name="Test Hotel")
    """

    # ── PayU credentials ────────────────────────────────────────────────
    payu_merchant_key: str = field(default_factory=lambda: os.getenv("PAYU_MERCHANT_KEY", ""))
    payu_merchant_salt: str = field(default_factory=lambda: os.getenv("PAYU_MERCHANT_SALT", ""))
    payu_mode: str = field(default_factory=lambda: os.getenv("PAYU_MODE", "test"))

    payu_test_url: str = field(default_factory=lambda: os.getenv("PAYU_TEST_URL", "https://test.payu.in/_payment"))
    payu_prod_url: str = field(default_factory=lambda: os.getenv("PAYU_PROD_URL", "https://secure.payu.in/_payment"))
    payu_test_verify_url: str = field(default_factory=lambda: os.getenv(
        "PAYU_TEST_VERIFY_URL", "https://test.payu.in/merchant/postservice?form=2"))
    payu_prod_verify_url: str = field(default_factory=lambda: os.getenv(
        "PAYU_PROD_VERIFY_URL", "https://info.payu.in/merchant/postservice?form=2"))

    # ── Server / networking ─────────────────────────────────────────────
    base_url: str = field(default_factory=lambda: os.getenv("BASE_URL", "http://localhost:9000"))
    server_host: str = field(default_factory=lambda: os.getenv("SERVER_HOST", "0.0.0.0"))
    server_port: int = field(default_factory=lambda: int(os.getenv("SERVER_PORT", "9000")))
    allowed_origins: list[str] = field(default_factory=lambda: _env_list("ALLOWED_ORIGINS", []))

    # ── Auth ─────────────────────────────────────────────────────────────
    # If set, every /api/* request must send this in the `X-API-Key` header.
    # Leave unset only for local dev — the worker will log a loud warning.
    api_key: str = field(default_factory=lambda: os.getenv("PAYU_WORKER_API_KEY", ""))

    # ── Hotel / business info ───────────────────────────────────────────
    hotel_name: str = field(default_factory=lambda: os.getenv("HOTEL_NAME", "Grand Hotel"))
    hotel_gst_number: str = field(default_factory=lambda: os.getenv("HOTEL_GST_NUMBER", ""))

    # ── Database ─────────────────────────────────────────────────────────
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "data/payments.db"))

    # ── Bill lifecycle ──────────────────────────────────────────────────
    # Duplicate create-bill calls for the same room+service+items within
    # this window return the existing pending bill instead of a new one.
    dedupe_window_seconds: int = field(default_factory=lambda: int(os.getenv("DEDUPE_WINDOW_SECONDS", "120")))
    # Pending bills older than this are auto-cancelled by the background sweep.
    pending_bill_ttl_minutes: int = field(default_factory=lambda: int(os.getenv("PENDING_BILL_TTL_MINUTES", "30")))

    # ── Misc ─────────────────────────────────────────────────────────────
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    request_id_header: str = "X-Request-ID"

    @property
    def payu_base_url(self) -> str:
        return self.payu_prod_url if self.payu_mode == "production" else self.payu_test_url

    @property
    def payu_verify_url(self) -> str:
        return self.payu_prod_verify_url if self.payu_mode == "production" else self.payu_test_verify_url

    def validate(self) -> list[str]:
        """
        Return a list of human-readable problems. Empty list == OK to start.
        Never raises — callers decide whether missing config is fatal.
        """
        problems = []
        if not self.payu_merchant_key or not self.payu_merchant_salt:
            problems.append(
                "PAYU_MERCHANT_KEY / PAYU_MERCHANT_SALT are not set. "
                "Get test credentials from https://devguide.payu.in/"
            )
        if self.payu_mode not in ("test", "production"):
            problems.append(f"PAYU_MODE must be 'test' or 'production', got {self.payu_mode!r}")
        if self.payu_mode == "production" and not self.api_key:
            problems.append(
                "Running in production PayU mode without PAYU_WORKER_API_KEY set — "
                "the billing API would be open to anyone. Set PAYU_WORKER_API_KEY."
            )
        if self.payu_mode == "production" and "*" in self.allowed_origins:
            problems.append("ALLOWED_ORIGINS must not be '*' in production.")
        return problems

    def masked_key_preview(self) -> str:
        if not self.payu_merchant_key:
            return "(unset)"
        return self.payu_merchant_key[:4] + "…"


def generate_api_key() -> str:
    """Helper for first-time setup: `python -c "from payu_worker.config import generate_api_key as g; print(g())"`"""
    return secrets.token_urlsafe(32)
