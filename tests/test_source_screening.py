"""Tests for the source-screening detector."""

from __future__ import annotations

from inflow_monitor.models.case import MonitoringCase
from inflow_monitor.skills.source_screening import SourceScreeningSkill
from tests.conftest import make_event


def test_sanctioned_source_is_critical(config):
    event = make_event(counterparty_id="cp_bad", source_country="XX")
    case = MonitoringCase(
        case_id="s1",
        event=event,
        enrichment={"source_sanctioned": True},
    )
    signal = SourceScreeningSkill(config).evaluate(case)
    assert signal is not None
    assert signal.critical is True
    assert signal.severity >= 90


def test_watchlisted_counterparty_flags_non_critical(config):
    event = make_event(counterparty_id="cp_watch")
    case = MonitoringCase(
        case_id="s2",
        event=event,
        enrichment={"counterparty_watchlist": ["cp_watch"]},
    )
    signal = SourceScreeningSkill(config).evaluate(case)
    assert signal is not None
    assert signal.critical is False
    assert signal.severity >= 70


def test_clean_source_is_silent(config):
    event = make_event(counterparty_id="cp_ok", source_country="US")
    case = MonitoringCase(case_id="s3", event=event)
    assert SourceScreeningSkill(config).evaluate(case) is None
