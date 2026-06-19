"""Decision agent: maps the risk score and signals to a monitoring outcome."""

from __future__ import annotations

from inflow_monitor.agents.base import Agent
from inflow_monitor.models.case import MonitoringCase
from inflow_monitor.models.decision import Decision, DecisionOutcome


class DecisionAgent(Agent):
    """Applies the monitoring policy to produce an explainable recommendation."""

    name = "decision"

    def run(self, case: MonitoringCase) -> Decision:
        policy = self.config.decision_policy
        score = case.risk_score

        if score >= policy.flag_threshold:
            outcome = DecisionOutcome.FLAG
            actions = [
                "Place a hold on the credited funds pending review.",
                "Open a suspicious-activity review (SAR candidate) with this case as evidence.",
                "Escalate to the AML investigations queue for a human decision.",
            ]
        elif score >= policy.review_threshold:
            outcome = DecisionOutcome.REVIEW
            actions = [
                "Route the case to an analyst for enhanced due diligence.",
                "Request source-of-funds documentation from the relationship owner.",
            ]
        else:
            outcome = DecisionOutcome.CLEAR
            actions = [
                "Release the credit and continue passive monitoring.",
            ]

        reasons = [signal.rationale for signal in case.triggered_signals()]
        if not reasons:
            reasons = ["No suspicion indicators were triggered for this inbound transaction."]

        confidence = self._confidence(case, outcome)
        decision = Decision(
            case_id=case.case_id,
            outcome=outcome,
            risk_score=score,
            confidence=confidence,
            reasons=reasons,
            recommended_actions=actions,
        )
        self.logger.info(
            "Decided %s: %s (risk=%.1f, confidence=%.2f)",
            case.case_id,
            outcome.value,
            score,
            confidence,
        )
        return decision

    def _confidence(self, case: MonitoringCase, outcome: DecisionOutcome) -> float:
        """Derive a confidence value from the score margin around thresholds."""
        policy = self.config.decision_policy
        score = case.risk_score

        if outcome is DecisionOutcome.FLAG:
            margin = (score - policy.flag_threshold) / max(100 - policy.flag_threshold, 1)
        elif outcome is DecisionOutcome.CLEAR:
            margin = (policy.review_threshold - score) / max(policy.review_threshold, 1)
        else:
            band = max(policy.flag_threshold - policy.review_threshold, 1)
            midpoint = (policy.flag_threshold + policy.review_threshold) / 2
            margin = 1.0 - abs(score - midpoint) / band

        base = 0.6 + 0.4 * max(0.0, min(1.0, margin))
        return round(max(0.0, min(1.0, base)), 2)
