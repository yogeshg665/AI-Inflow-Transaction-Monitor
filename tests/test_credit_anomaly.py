"""Tests for the credit-anomaly detector."""

from __future__ import annotations

from inflow_monitor.models.case import MonitoringCase
from inflow_monitor.skills.credit_anomaly import CreditAnomalySkill
from tests.conftest import make_event


def _history() -> list:
    return [
        make_event(event_id="h1", amount=2000.0),
        make_event(event_id="h2", amount=2100.0),
        make_event(event_id="h3", amount=1900.0),
    ]


def test_large_outlier_credit_flags(config):
    event = make_event(amount=60000.0)
    case = MonitoringCase(case_id="a1", event=event, account_history=_history())
    signal = CreditAnomalySkill(config).evaluate(case)
    assert signal is not None
    assert signal.name == "anomalous_credit"
    assert signal.evidence.get("baseline_multiple", 0) >= 5


def test_in_range_credit_is_silent(config):
    event = make_event(amount=2050.0)
    case = MonitoringCase(case_id="a2", event=event, account_history=_history())
    assert CreditAnomalySkill(config).evaluate(case) is None


def test_insufficient_history_is_silent(config):
    event = make_event(amount=60000.0)
    history = [make_event(event_id="h1", amount=2000.0)]
    case = MonitoringCase(case_id="a3", event=event, account_history=history)
    assert CreditAnomalySkill(config).evaluate(case) is None
