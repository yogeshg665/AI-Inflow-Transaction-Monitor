"""Orchestrator agent: composes all stages into one monitoring workflow."""

from __future__ import annotations

from inflow_monitor.agents.base import Agent
from inflow_monitor.agents.decision_agent import DecisionAgent
from inflow_monitor.agents.detection_swarm import DetectionSwarmAgent
from inflow_monitor.agents.enrichment_agent import EnrichmentAgent
from inflow_monitor.agents.intake_agent import IntakeAgent
from inflow_monitor.agents.reporting_agent import ReportingAgent
from inflow_monitor.agents.risk_scoring_agent import RiskScoringAgent
from inflow_monitor.llm.client import LLMClient
from inflow_monitor.memory.store import MemoryStore
from inflow_monitor.models.case import MonitoringCase
from inflow_monitor.models.decision import Decision
from inflow_monitor.models.movement import MovementEvent
from inflow_monitor.utils.config import EngineConfig


class MonitoringResult:
    """Container bundling the outcome of a single monitored case."""

    def __init__(self, decision: Decision, report: dict) -> None:
        self.decision = decision
        self.report = report


class OrchestratorAgent(Agent):
    """Runs intake, enrichment, recall, detection, scoring, decision, reporting."""

    name = "orchestrator"

    def __init__(
        self,
        config: EngineConfig,
        llm_client: LLMClient | None = None,
        memory_store: MemoryStore | None = None,
    ) -> None:
        super().__init__(config)
        self.intake = IntakeAgent(config)
        self.enrichment = EnrichmentAgent(config)
        self.swarm = DetectionSwarmAgent(config)
        self.scoring = RiskScoringAgent(config)
        self.decision = DecisionAgent(config)
        self.reporting = ReportingAgent(config, llm_client=llm_client)
        self.memory_store = memory_store

    def investigate(
        self,
        event: MovementEvent,
        account_history: list[MovementEvent] | None = None,
        enrichment: dict | None = None,
    ) -> MonitoringResult:
        """Execute the full monitoring workflow for one inbound event."""
        case = self.intake.run(event, account_history)
        if enrichment:
            case.enrichment.update(enrichment)
        case = self.enrichment.run(case)
        self._recall_history(case)
        case = self.swarm.run(case)
        case = self.scoring.run(case)
        decision = self.decision.run(case)
        report = self.reporting.run(case, decision)
        self._remember(case, decision)
        return MonitoringResult(decision=decision, report=report)

    def _recall_history(self, case: MonitoringCase) -> None:
        """Inject prior-case history from collective memory, when available."""
        if self.memory_store is None:
            return
        summary = self.memory_store.recall_similar(case.event)
        if summary.has_history:
            case.enrichment["memory_recall"] = summary.as_enrichment()

    def _remember(self, case: MonitoringCase, decision: Decision) -> None:
        """Persist the completed case to collective memory."""
        if self.memory_store is None:
            return
        self.memory_store.record_investigation(case, decision)
