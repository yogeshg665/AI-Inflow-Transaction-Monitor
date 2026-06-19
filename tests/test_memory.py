"""Tests for the collective-memory, recall, feedback, and calibration layer."""

from __future__ import annotations

from datetime import datetime, timezone

from inflow_monitor.memory import (
    CaseMemoryRecord,
    FeedbackLabel,
    MemoryStore,
    calibrate_thresholds,
)
from inflow_monitor.models.case import MonitoringCase
from inflow_monitor.models.decision import Decision, DecisionOutcome
from inflow_monitor.pipeline import MonitoringPipeline
from inflow_monitor.pipeline.monitoring_pipeline import CaseInput
from inflow_monitor.skills.prior_history import PriorHistorySkill
from inflow_monitor.utils.config import load_config
from tests.conftest import make_event


def _enable_memory(tmp_path):
    config = load_config()
    config.memory.enabled = True
    config.memory.path = str(tmp_path / "memory.db")
    return config


def _persist(store: MemoryStore, case_id: str, outcome: DecisionOutcome, score: float):
    event = make_event(event_id=case_id, account_id="acct_repeat")
    case = MonitoringCase(case_id=case_id, event=event, risk_score=score)
    decision = Decision(
        case_id=case_id,
        outcome=outcome,
        risk_score=score,
        confidence=0.8,
        narrative="n",
    )
    return store.record_investigation(case, decision)


def test_recall_returns_prior_history(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    _persist(store, "case_a", DecisionOutcome.FLAG, 80.0)
    summary = store.recall_similar(make_event(account_id="acct_repeat"))
    assert summary.has_history is True
    assert summary.total_prior_cases == 1
    assert summary.prior_flag_count == 1
    store.close()


def test_feedback_returns_false_for_unknown_case(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    assert store.record_feedback("missing", FeedbackLabel.CLEARED) is False
    store.close()


def test_feedback_is_recorded_and_recalled(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    _persist(store, "case_a", DecisionOutcome.FLAG, 80.0)
    assert store.record_feedback("case_a", FeedbackLabel.CONFIRMED_SUSPICIOUS) is True
    summary = store.recall_similar(make_event(account_id="acct_repeat"))
    assert summary.confirmed_suspicious_count == 1
    store.close()


def test_prior_history_signal_from_recall(config):
    event = make_event()
    case = MonitoringCase(
        case_id="ph1",
        event=event,
        enrichment={
            "memory_recall": {
                "total_prior_cases": 2,
                "confirmed_suspicious_count": 2,
                "prior_flag_count": 1,
                "prior_review_count": 0,
                "matched_on": "account",
            }
        },
    )
    signal = PriorHistorySkill(config).evaluate(case)
    assert signal is not None
    assert signal.name == "adverse_prior_history"
    assert signal.critical is False
    assert signal.severity > 0


def test_calibration_requires_both_labels(config):
    record = CaseMemoryRecord(
        case_id="c1",
        account_id="a",
        counterparty_id="cp",
        amount=1.0,
        currency="USD",
        occurred_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        risk_score=80.0,
        outcome="flag",
        label=FeedbackLabel.CONFIRMED_SUSPICIOUS,
        recorded_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
    )
    report = calibrate_thresholds([record], config.decision_policy)
    assert report.suggested_flag_threshold is None


def test_calibration_separable_labels(config):
    def record(case_id, score, label):
        return CaseMemoryRecord(
            case_id=case_id,
            account_id="a",
            counterparty_id="cp",
            amount=1.0,
            currency="USD",
            occurred_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
            risk_score=score,
            outcome="flag" if label is FeedbackLabel.CONFIRMED_SUSPICIOUS else "clear",
            label=label,
            recorded_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

    records = [
        record("s1", 90.0, FeedbackLabel.CONFIRMED_SUSPICIOUS),
        record("s2", 80.0, FeedbackLabel.CONFIRMED_SUSPICIOUS),
        record("c1", 20.0, FeedbackLabel.CLEARED),
        record("c2", 30.0, FeedbackLabel.CLEARED),
    ]
    report = calibrate_thresholds(records, config.decision_policy)
    assert report.suggested_flag_threshold == 55.0


def test_pipeline_persists_and_recalls(tmp_path):
    config = _enable_memory(tmp_path)
    pipeline = MonitoringPipeline(config=config)
    assert pipeline.memory_store is not None
    event = make_event(event_id="evt_first", account_id="acct_seen", amount=1500.0)
    pipeline.run_one(CaseInput(event=event))
    second = make_event(event_id="evt_second", account_id="acct_seen", amount=1600.0)
    result = pipeline.run_one(CaseInput(event=second))
    recall = result.report  # report exists; recall summary stored on enrichment
    assert recall["case_id"]
    assert pipeline.memory_store.stats()["total"] == 2
