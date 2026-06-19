"""Funds-movement value object for inbound-transaction monitoring.

The model intentionally avoids storing raw banking instrument data. Accounts and
counterparties are referenced through pseudonymous identifiers, and any payment
instrument is represented by an opaque token, so the engine can operate without
handling sensitive customer data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MovementEvent(BaseModel):
    """A single inbound or outbound money movement on a monitored account.

    The event under monitoring is always an inbound credit. Prior movements in
    both directions are supplied as account history so the detectors can reason
    about velocity, structuring, and pass-through behavior.
    """

    event_id: str = Field(..., description="Unique movement identifier.")
    account_id: str = Field(..., description="Pseudonymous beneficiary account identifier.")
    counterparty_id: str = Field(
        ..., description="Pseudonymous originator or source identifier."
    )
    direction: str = Field(
        default="inbound", description="Movement direction: 'inbound' or 'outbound'."
    )
    amount: float = Field(..., ge=0.0, description="Movement amount in major currency units.")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    value_date: datetime = Field(..., description="UTC time the funds settled.")
    channel: str = Field(
        default="ach",
        description="Rail used: ach, wire, cash, check, p2p, crypto_onramp, card_refund.",
    )
    source_country: str = Field(
        default="US",
        min_length=2,
        max_length=2,
        description="ISO 3166-1 alpha-2 country the funds originated from.",
    )
    account_country: str = Field(
        default="US",
        min_length=2,
        max_length=2,
        description="ISO 3166-1 alpha-2 country where the account is booked.",
    )
    counterparty_type: str = Field(
        default="unknown", description="Originator type: individual, business, or unknown."
    )
    instrument_token: Optional[str] = Field(
        default=None, description="Opaque token for the originating instrument, if any."
    )
    memo: Optional[str] = Field(
        default=None, description="Short, non-identifying reference descriptor."
    )

    @property
    def is_inbound(self) -> bool:
        """Whether this movement is an inbound credit."""
        return self.direction.lower() == "inbound"

    def amount_label(self) -> str:
        """Return a human-readable amount with currency for reporting."""
        return f"{self.amount:,.2f} {self.currency}"
