"""Tests for the cross-border detector."""

from __future__ import annotations

from inflow_monitor.models.case import MonitoringCase
from inflow_monitor.skills.cross_border import CrossBorderRiskSkill
from tests.conftest import make_event


def test_cross_border_and_currency_mismatch_flags(config):
    event = make_event(currency="EUR", source_country="GB", account_country="US")
    case = MonitoringCase(case_id="x1", event=event)
    signal = CrossBorderRiskSkill(config).evaluate(case)
    assert signal is not None
    assert signal.name == "cross_border_inflow"
    assert signal.evidence.get("currency") == "EUR"
    assert signal.severity >= 50


def test_domestic_same_currency_is_silent(config):
    event = make_event(currency="USD", source_country="US", account_country="US")
    case = MonitoringCase(case_id="x2", event=event)
    assert CrossBorderRiskSkill(config).evaluate(case) is None
