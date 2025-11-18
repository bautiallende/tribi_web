from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


def to_minor_units(amount: Decimal | float | str) -> int:
    """Convert a decimal currency amount into integer minor units (e.g., cents)."""
    decimal_amount = Decimal(str(amount)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return int(decimal_amount * 100)


def format_minor_units(
    amount_minor_units: int, currency: str = "USD"
) -> dict[str, str | int]:
    """Return display helper for minor units (major amount string + currency)."""
    major = Decimal(amount_minor_units) / Decimal(100)
    return {
        "currency": currency,
        "amount_minor_units": amount_minor_units,
        "amount_major": f"{major:.2f}",
    }
