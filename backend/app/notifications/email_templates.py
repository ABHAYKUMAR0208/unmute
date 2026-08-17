"""
email_templates.py — HTML email templates shared by taxi bookings and
PayU payment-link notifications.

Keeping templates in one place means both notification paths (taxi_worker.py
and payments/payment_bridge.py) get the same branding, and rebranding is a
one-line change (HOTEL_NAME / ACCENT_COLOR below) instead of hunting through
multiple files for hardcoded strings.

Email HTML has to be old-school: inline styles only, table-based layout,
no flexbox/grid — Gmail, Outlook, and mobile mail clients strip or ignore
anything else.
"""

from __future__ import annotations

import os

HOTEL_NAME = os.getenv("HOTEL_NAME", "Grandview Hotel")
ACCENT_COLOR = "#0f4c81"   # navy — swap for your brand color
ACCENT_LIGHT = "#eaf1f8"
TEXT_COLOR = "#1f2933"
MUTED_COLOR = "#6b7280"
BORDER_COLOR = "#e5e7eb"


def _base_wrapper(preheader: str, body_html: str) -> str:
    """Wraps any inner content in the shared header/footer chrome."""
    return f"""\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{HOTEL_NAME}</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f5f7;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
  <!-- Preheader: hidden preview text shown in inbox list -->
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;">{preheader}</div>

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f7;padding:32px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.08);">

          <!-- Header -->
          <tr>
            <td style="background-color:{ACCENT_COLOR};padding:28px 32px;">
              <span style="color:#ffffff;font-size:20px;font-weight:600;letter-spacing:0.3px;">{HOTEL_NAME}</span>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:32px;">
              {body_html}
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:20px 32px;background-color:#fafafa;border-top:1px solid {BORDER_COLOR};">
              <p style="margin:0;font-size:12px;color:{MUTED_COLOR};line-height:1.5;">
                This is an automated message from {HOTEL_NAME}. Please do not reply directly to this email.
                Need help? Contact the front desk any time.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def _detail_row(label: str, value: str) -> str:
    return f"""\
        <tr>
          <td style="padding:6px 0;font-size:14px;color:{MUTED_COLOR};width:40%;">{label}</td>
          <td style="padding:6px 0;font-size:14px;color:{TEXT_COLOR};font-weight:600;">{value}</td>
        </tr>"""


def _section_card(title: str, rows_html: str) -> str:
    return f"""\
    <p style="margin:0 0 8px 0;font-size:13px;font-weight:600;color:{ACCENT_COLOR};text-transform:uppercase;letter-spacing:0.5px;">{title}</p>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{ACCENT_LIGHT};border-radius:6px;padding:16px 20px;margin-bottom:24px;">
      {rows_html}
    </table>"""


def _cta_button(url: str, label: str) -> str:
    return f"""\
    <table role="presentation" cellpadding="0" cellspacing="0" style="margin:8px 0 4px 0;">
      <tr>
        <td style="border-radius:6px;background-color:{ACCENT_COLOR};">
          <a href="{url}" target="_blank"
             style="display:inline-block;padding:12px 28px;font-size:14px;font-weight:600;color:#ffffff;text-decoration:none;border-radius:6px;">
            {label}
          </a>
        </td>
      </tr>
    </table>"""


# ── Taxi booking confirmation ────────────────────────────────────────────

def render_taxi_confirmation(booking_id: str, guest, driver: dict) -> tuple[str, str]:
    """Returns (subject, html_body) for the taxi booking confirmation email."""
    subject = f"Taxi Booking Confirmed — {booking_id}"

    booking_rows = "".join([
        _detail_row("Booking ID", booking_id),
        _detail_row("Room Number", guest.room_number),
        _detail_row("Destination", guest.destination),
        _detail_row("Pickup From", guest.pickup_location),
        _detail_row("Pickup Time", guest.pickup_time),
    ])
    driver_rows = "".join([
        _detail_row("Driver Name", driver["name"]),
        _detail_row("Driver Phone", driver["phone"]),
        _detail_row("Vehicle Number", driver["vehicle"]),
    ])

    body_html = f"""\
    <p style="margin:0 0 4px 0;font-size:18px;font-weight:600;color:{TEXT_COLOR};">Your taxi is confirmed</p>
    <p style="margin:0 0 24px 0;font-size:14px;color:{MUTED_COLOR};">Dear {guest.guest_name}, here are your booking details.</p>

    {_section_card("Booking Details", booking_rows)}
    {_section_card("Driver Details", driver_rows)}

    <p style="margin:0;font-size:14px;color:{TEXT_COLOR};">
      Please be ready at <strong>{guest.pickup_location}</strong> at <strong>{guest.pickup_time}</strong>.
      Have a safe journey!
    </p>
    """

    return subject, _base_wrapper(f"Your taxi booking {booking_id} is confirmed", body_html)


# ── Bill / payment link email ────────────────────────────────────────────

def render_bill_email(guest_name: str, service_label: str, bill_id: str,
                       room_number: str, items_rows_html: str,
                       subtotal: str, tax_label: str, tax_amount: str,
                       total: str, payment_link: str) -> tuple[str, str]:
    """Returns (subject, html_body) for the bill/payment-link email."""
    subject = "Your bill is ready — pay online"

    info_rows = "".join([
        _detail_row("Bill ID", bill_id),
        _detail_row("Room Number", room_number),
        _detail_row("Service", service_label),
    ])

    body_html = f"""\
    <p style="margin:0 0 4px 0;font-size:18px;font-weight:600;color:{TEXT_COLOR};">Your bill is ready</p>
    <p style="margin:0 0 24px 0;font-size:14px;color:{MUTED_COLOR};">Dear {guest_name}, thank you for your order.</p>

    {_section_card("Bill Summary", info_rows)}

    <p style="margin:0 0 8px 0;font-size:13px;font-weight:600;color:{ACCENT_COLOR};text-transform:uppercase;letter-spacing:0.5px;">Items</p>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin-bottom:16px;">
      <tr style="border-bottom:1px solid {BORDER_COLOR};">
        <td style="padding:8px 0;font-size:12px;color:{MUTED_COLOR};text-transform:uppercase;">Item</td>
        <td style="padding:8px 0;font-size:12px;color:{MUTED_COLOR};text-transform:uppercase;text-align:right;">Amount</td>
      </tr>
      {items_rows_html}
      <tr>
        <td style="padding:10px 0 2px 0;font-size:14px;color:{MUTED_COLOR};">Subtotal</td>
        <td style="padding:10px 0 2px 0;font-size:14px;color:{TEXT_COLOR};text-align:right;">{subtotal}</td>
      </tr>
      <tr>
        <td style="padding:2px 0;font-size:14px;color:{MUTED_COLOR};">{tax_label}</td>
        <td style="padding:2px 0;font-size:14px;color:{TEXT_COLOR};text-align:right;">{tax_amount}</td>
      </tr>
      <tr>
        <td style="padding:10px 0 0 0;font-size:16px;font-weight:700;color:{TEXT_COLOR};border-top:1px solid {BORDER_COLOR};">Total</td>
        <td style="padding:10px 0 0 0;font-size:16px;font-weight:700;color:{ACCENT_COLOR};text-align:right;border-top:1px solid {BORDER_COLOR};">{total}</td>
      </tr>
    </table>

    {_cta_button(payment_link, "Pay Now")}
    <p style="margin:12px 0 0 0;font-size:12px;color:{MUTED_COLOR};">
      Or copy this link into your browser:<br>
      <a href="{payment_link}" style="color:{ACCENT_COLOR};word-break:break-all;">{payment_link}</a>
    </p>
    """

    return subject, _base_wrapper("Your bill is ready — pay online", body_html)