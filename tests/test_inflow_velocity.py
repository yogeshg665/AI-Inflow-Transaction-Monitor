"""Tests for the inflow-velocity detector."""

from __future__ import annotations

from datetime import datetime, timezone

from inflow_monitor.models.case import MonitoringCase
from inflow_monitor.skills.inflow_velocity import InflowVelocitySkill
from tests.conftest import make_event


def test_inbound_burst_flags(config):
    base = datetime(2026, 5, 6, 18, 0, tzinfo=timezone.utc)
    event = make_event(amount=4200.0, value_date=base)
    history = [
        make_event(
            event_id=f"h{i}",
            counterparty_id=f"cp_{i}",
            amount=3800.0,
            value_date=datetime(2026, 5, 6, 6 + i, 0, tzinfo=timezone.utc),
        )
        for i in range(4)
    ]
    case = MonitoringCase(case_id="v1", event=event, account_history=history)
    signal = InflowVelocitySkill(config).evaluate(case)
    assert signal is not None
    assert signal.name == "inbound_velocity_burst"
    assert signal.evidence["inbound_count"] == 5


def test_quiet_account_is_silent(config):
    event = make_event(amount=2000.0)
    case = MonitoringCase(case_id="v2", event=event)
    assert InflowVelocitySkill(config).evaluate(case) is None
