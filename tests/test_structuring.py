"""Tests for the structuring detector."""

from __future__ import annotations

from datetime import datetime, timezone

from inflow_monitor.models.case import MonitoringCase
from inflow_monitor.skills.structuring import StructuringDetectionSkill
from tests.conftest import make_event


def test_near_threshold_single_credit_flags(config):
    event = make_event(amount=9600.0)
    case = MonitoringCase(case_id="c1", event=event)
    signal = StructuringDetectionSkill(config).evaluate(case)
    assert signal is not None
    assert signal.name == "potential_structuring"
    assert signal.severity > 0


def test_aggregated_sub_threshold_flags(config):
    base = datetime(2026, 5, 3, 16, 0, tzinfo=timezone.utc)
    event = make_event(amount=9600.0, value_date=base)
    history = [
        make_event(
            event_id="h1",
            amount=9400.0,
            value_date=datetime(2026, 5, 2, 11, 0, tzinfo=timezone.utc),
        ),
        make_event(
            event_id="h2",
            amount=9700.0,
            value_date=datetime(2026, 5, 1, 18, 0, tzinfo=timezone.utc),
        ),
    ]
    case = MonitoringCase(case_id="c2", event=event, account_history=history)
    signal = StructuringDetectionSkill(config).evaluate(case)
    assert signal is not None
    assert signal.evidence.get("sub_threshold_count") == 3


def test_normal_credit_is_silent(config):
    event = make_event(amount=1500.0)
    case = MonitoringCase(case_id="c3", event=event)
    assert StructuringDetectionSkill(config).evaluate(case) is None
