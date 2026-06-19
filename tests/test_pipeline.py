"""End-to-end pipeline and decision tests."""

from __future__ import annotations

from inflow_monitor.models.decision import DecisionOutcome
from inflow_monitor.pipeline import MonitoringPipeline, load_cases_from_json
from inflow_monitor.pipeline.monitoring_pipeline import CaseInput
from tests.conftest import make_event


def test_sanctioned_inflow_is_flagged():
    pipeline = MonitoringPipeline()
    event = make_event(amount=12000.0, currency="EUR", source_country="XX")
    case = CaseInput(event=event, enrichment={"source_sanctioned": True})
    result = pipeline.run_one(case)
    assert result.decision.outcome is DecisionOutcome.FLAG
    assert result.decision.is_actionable_by_human() is True
    assert any(s["name"] == "high_risk_source" for s in result.report["signals"])


def test_clean_inflow_is_cleared():
    pipeline = MonitoringPipeline()
    event = make_event(amount=1500.0)
    result = pipeline.run_one(CaseInput(event=event))
    assert result.decision.outcome is DecisionOutcome.CLEAR
    assert result.decision.is_actionable_by_human() is False


def test_report_contains_reasoning_trail():
    pipeline = MonitoringPipeline()
    event = make_event(amount=9600.0, channel="cash")
    result = pipeline.run_one(CaseInput(event=event))
    assert "reasoning" in result.report
    assert isinstance(result.report["reasoning"], list)


def test_batch_runs_over_sample_dataset():
    pipeline = MonitoringPipeline()
    cases = load_cases_from_json("data/samples/sample_inflows.json")
    results = pipeline.run_batch(cases)
    assert len(results) == len(cases)
    outcomes = {r.report["case_id"]: r.decision.outcome for r in results}
    assert all(o in set(DecisionOutcome) for o in outcomes.values())


def test_memory_disabled_by_default():
    pipeline = MonitoringPipeline()
    assert pipeline.memory_store is None
