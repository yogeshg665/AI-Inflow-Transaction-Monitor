"""Shared pytest fixtures and builders."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from inflow_monitor.models.movement import MovementEvent
from inflow_monitor.utils.config import load_config


def make_event(
    event_id: str = "evt_test",
    account_id: str = "acct_test",
    counterparty_id: str = "cp_test",
    direction: str = "inbound",
    amount: float = 2000.0,
    currency: str = "USD",
    value_date: datetime | None = None,
    channel: str = "ach",
    source_country: str = "US",
    account_country: str = "US",
) -> MovementEvent:
    """Construct a movement event with sensible defaults for tests."""
    return MovementEvent(
        event_id=event_id,
        account_id=account_id,
        counterparty_id=counterparty_id,
        direction=direction,
        amount=amount,
        currency=currency,
        value_date=value_date or datetime(2026, 5, 1, 14, 0, tzinfo=timezone.utc),
        channel=channel,
        source_country=source_country,
        account_country=account_country,
    )


@pytest.fixture()
def config():
    return load_config()
