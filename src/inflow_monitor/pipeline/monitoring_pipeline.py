"""High-level pipeline for batch and single-case monitoring.

The pipeline wraps the orchestrator with input loading and optional report
persistence, providing a stable entry point for application code and the CLI.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from inflow_monitor.agents.orchestrator import MonitoringResult, OrchestratorAgent
from inflow_monitor.llm.client import LLMClient
from inflow_monitor.memory import (
    CalibrationReport,
    FeedbackLabel,
    MemoryStore,
    calibrate_thresholds,
)
from inflow_monitor.models.movement import MovementEvent
from inflow_monitor.utils.config import EngineConfig, load_config
from inflow_monitor.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CaseInput:
    """Normalized input for a single monitored case."""

    event: MovementEvent
    account_history: list[MovementEvent] = field(default_factory=list)
    enrichment: dict[str, Any] = field(default_factory=dict)


def load_cases_from_json(path: str | Path) -> list[CaseInput]:
    """Load monitoring inputs from a JSON file.

    The file must contain a list of objects, each with an ``event`` object and
    optional ``account_history`` (list) and ``enrichment`` (object).
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Input JSON must be a list of case objects.")

    cases: list[CaseInput] = []
    for entry in raw:
        event = MovementEvent.model_validate(entry["event"])
        history = [
            MovementEvent.model_validate(item) for item in entry.get("account_history", [])
        ]
        cases.append(
            CaseInput(
                event=event,
                account_history=history,
                enrichment=entry.get("enrichment", {}) or {},
            )
        )
    return cases


class MonitoringPipeline:
    """Coordinates monitoring over one or many cases."""

    def __init__(
        self,
        config: EngineConfig | None = None,
        llm_client: LLMClient | None = None,
        memory_store: MemoryStore | None = None,
    ) -> None:
        self.config = config or load_config()
        self.memory_store = memory_store or self._build_memory_store()
        self.orchestrator = OrchestratorAgent(
            self.config,
            llm_client=llm_client,
            memory_store=self.memory_store,
        )

    def _build_memory_store(self) -> MemoryStore | None:
        """Open the configured memory store, or return None when disabled."""
        if not self.config.memory.enabled:
            return None
        return MemoryStore(self.config.memory.path)

    def record_feedback(
        self,
        case_id: str,
        label: FeedbackLabel,
        note: str | None = None,
    ) -> bool:
        """Record an analyst-confirmed outcome for a previously stored case."""
        if self.memory_store is None:
            raise RuntimeError(
                "Collective memory is disabled. Enable memory in configuration to "
                "record feedback."
            )
        return self.memory_store.record_feedback(case_id, label, note)

    def calibrate(self) -> CalibrationReport:
        """Recommend decision thresholds from labeled feedback."""
        if self.memory_store is None:
            raise RuntimeError(
                "Collective memory is disabled. Enable memory in configuration to "
                "calibrate thresholds."
            )
        return calibrate_thresholds(
            self.memory_store.all_records(),
            self.config.decision_policy,
        )

    def run_one(self, case_input: CaseInput) -> MonitoringResult:
        """Monitor a single case."""
        return self.orchestrator.investigate(
            event=case_input.event,
            account_history=case_input.account_history,
            enrichment=case_input.enrichment,
        )

    def run_batch(
        self,
        cases: Iterable[CaseInput],
        output_dir: str | Path | None = None,
    ) -> list[MonitoringResult]:
        """Monitor a batch of cases, optionally persisting JSON reports."""
        results: list[MonitoringResult] = []
        out_path = Path(output_dir) if output_dir else None
        if out_path is not None:
            out_path.mkdir(parents=True, exist_ok=True)

        for case_input in cases:
            result = self.run_one(case_input)
            results.append(result)
            if out_path is not None and self.config.engine.persist_reports:
                report_file = out_path / f"{result.report['case_id']}.json"
                report_file.write_text(
                    json.dumps(result.report, indent=2), encoding="utf-8"
                )

        logger.info("Completed batch of %d case(s)", len(results))
        return results
