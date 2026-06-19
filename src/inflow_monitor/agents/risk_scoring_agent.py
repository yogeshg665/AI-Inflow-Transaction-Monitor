"""Risk scoring agent: aggregates detector signals into a single score.

The aggregate score is a confidence-weighted, configuration-weighted blend of
individual signal severities, bounded to the 0-100 range. Using a blend rather
than a simple maximum keeps the score robust to a single noisy detector while
still reacting strongly to multiple corroborating indicators. A definitive
(critical) hit, such as a sanctioned source, sets a floor on the score.
"""

from __future__ import annotations

from inflow_monitor.agents.base import Agent
from inflow_monitor.models.case import MonitoringCase


class RiskScoringAgent(Agent):
    """Computes the aggregate risk score from signals already on the case."""

    name = "risk_scoring"

    def run(self, case: MonitoringCase) -> MonitoringCase:
        case.risk_score = self._aggregate(case)
        self.logger.info(
            "Scored %s: risk=%.1f from %d signal(s)",
            case.case_id,
            case.risk_score,
            len(case.triggered_signals()),
        )
        return case

    def _aggregate(self, case: MonitoringCase) -> float:
        weights = self.config.skill_weights
        triggered = case.triggered_signals()
        if not triggered:
            return 0.0

        weighted_sum = 0.0
        weight_total = 0.0
        for signal in triggered:
            weight = weights.get(signal.skill, 0.1) * signal.confidence
            weighted_sum += signal.severity * weight
            weight_total += weight

        blended = weighted_sum / weight_total if weight_total else 0.0

        # Apply a corroboration boost: multiple independent triggers raise risk.
        corroboration = min(0.25, 0.05 * (len(triggered) - 1))
        score = blended * (1.0 + corroboration)

        # A definitive (critical) indicator sets a floor on the score so it
        # cannot be diluted by weaker signals.
        critical_floor = max(
            (signal.severity for signal in triggered if signal.critical),
            default=0.0,
        )
        score = max(score, critical_floor)
        return round(max(0.0, min(100.0, score)), 1)
