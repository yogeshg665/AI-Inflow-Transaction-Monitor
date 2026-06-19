"""Reporting agent: produces an explainable, audit-ready monitoring report."""

from __future__ import annotations

from inflow_monitor.agents.base import Agent
from inflow_monitor.llm.client import LLMClient
from inflow_monitor.models.case import MonitoringCase
from inflow_monitor.models.decision import Decision

_SYSTEM_PROMPT = (
    "You are a senior AML transaction-monitoring analyst. Write a concise, "
    "factual case summary for an audit trail and a potential suspicious-activity "
    "filing. Use neutral, professional language. Do not invent facts beyond the "
    "provided signals and decision."
)


class ReportingAgent(Agent):
    """Generates a structured report and a human-readable narrative."""

    name = "reporting"

    def __init__(self, config, llm_client: LLMClient | None = None) -> None:
        super().__init__(config)
        self.llm = llm_client or LLMClient()

    def run(self, case: MonitoringCase, decision: Decision) -> dict:
        narrative = self._build_narrative(case, decision)
        decision.narrative = narrative

        triggered = case.triggered_signals()
        report = {
            "case_id": case.case_id,
            "created_at": case.created_at.isoformat(),
            "event": {
                "event_id": case.event.event_id,
                "account_id": case.event.account_id,
                "counterparty_id": case.event.counterparty_id,
                "direction": case.event.direction,
                "amount": case.event.amount,
                "currency": case.event.currency,
                "channel": case.event.channel,
                "source_country": case.event.source_country,
                "account_country": case.event.account_country,
                "value_date": case.event.value_date.isoformat(),
            },
            "risk_score": case.risk_score,
            "decision": decision.outcome.value,
            "confidence": decision.confidence,
            "signals": [
                {
                    "detector": signal.skill,
                    "name": signal.name,
                    "severity": signal.severity,
                    "confidence": signal.confidence,
                    "critical": signal.critical,
                    "rationale": signal.rationale,
                    "evidence": signal.evidence,
                }
                for signal in triggered
            ],
            # Explicit reasoning trail: one line of justification per fired signal.
            "reasoning": [f"{signal.name}: {signal.rationale}" for signal in triggered],
            "recommended_actions": decision.recommended_actions,
            "narrative": narrative,
        }
        self.logger.info("Generated report for %s", case.case_id)
        return report

    def _build_narrative(self, case: MonitoringCase, decision: Decision) -> str:
        """Use the LLM when available; otherwise build a deterministic summary."""
        deterministic = self._deterministic_narrative(case, decision)
        generated = self.llm.summarize(_SYSTEM_PROMPT, deterministic)
        return generated or deterministic

    @staticmethod
    def _deterministic_narrative(case: MonitoringCase, decision: Decision) -> str:
        event = case.event
        lines = [
            f"Case {case.case_id} monitored inbound event {event.event_id} for "
            f"{event.amount_label()} into account {event.account_id} from "
            f"counterparty {event.counterparty_id} via {event.channel}.",
            f"Aggregate risk score: {case.risk_score:.1f}/100. "
            f"Recommendation: {decision.outcome.value.upper()} "
            f"(confidence {decision.confidence:.0%}).",
        ]
        triggered = case.triggered_signals()
        if triggered:
            lines.append("Contributing indicators:")
            for signal in triggered:
                lines.append(f"- {signal.rationale}")
        else:
            lines.append("No suspicion indicators were triggered.")
        lines.append("Recommended actions:")
        for action in decision.recommended_actions:
            lines.append(f"- {action}")
        return "\n".join(lines)
