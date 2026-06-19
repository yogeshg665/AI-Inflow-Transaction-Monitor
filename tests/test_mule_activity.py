"""Tests for the mule-activity detector."""

from __future__ import annotations

from datetime import datetime, timezone

from inflow_monitor.models.case import MonitoringCase
from inflow_monitor.skills.mule_activity import MuleActivitySkill
from tests.conftest import make_event


def test_rapid_passthrough_flags(config):
    base = datetime(2026, 5, 4, 9, 0, tzinfo=timezone.utc)
    event = make_event(amount=8000.0, value_date=base)
    history = [
        make_event(
            event_id="o1",
            direction="outbound",
            amount=4000.0,
            value_date=datetime(2026, 5, 4, 10, 30, tzinfo=timezone.utc),
        ),
        make_event(
            event_id="o2",
            direction="outbound",
            amount=3600.0,
            value_date=datetime(2026, 5, 4, 14, 0, tzinfo=timezone.utc),
        ),
    ]
    case = MonitoringCase(case_id="m1", event=event, account_history=history)
    signal = MuleActivitySkill(config).evaluate(case)
    assert signal is not None
    assert signal.name == "rapid_passthrough"
    assert signal.evidence["passthrough_ratio"] >= 0.8


def test_no_outbound_is_silent(config):
    event = make_event(amount=8000.0)
    case = MonitoringCase(case_id="m2", event=event)
    assert MuleActivitySkill(config).evaluate(case) is None


def test_small_credit_below_minimum_is_silent(config):
    base = datetime(2026, 5, 4, 9, 0, tzinfo=timezone.utc)
    event = make_event(amount=500.0, value_date=base)
    history = [
        make_event(
            event_id="o1",
            direction="outbound",
            amount=500.0,
            value_date=datetime(2026, 5, 4, 10, 0, tzinfo=timezone.utc),
        ),
    ]
    case = MonitoringCase(case_id="m3", event=event, account_history=history)
    assert MuleActivitySkill(config).evaluate(case) is None
