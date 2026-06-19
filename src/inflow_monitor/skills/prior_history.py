"""Prior-history detector: turns recalled collective memory into a signal.

This detector is the read side of the optional collective-memory layer. The
orchestrator injects a recall summary into ``case.enrichment["memory_recall"]``
before detection runs; this skill reads that summary and emits a corroborating,
never-critical signal when an account or counterparty has adverse prior history.
It performs no I/O itself, so it stays deterministic and side-effect free.
"""

from __future__ import annotations

from typing import Optional

from inflow_monitor.models.case import MonitoringCase, RiskSignal
from inflow_monitor.skills.base import Skill


class PriorHistorySkill(Skill):
    """Raises risk when memory recall shows adverse history for this entity."""

    name = "prior_history"

    def evaluate(self, case: MonitoringCase) -> Optional[RiskSignal]:
        recall = case.enrichment.get("memory_recall")
        if not isinstance(recall, dict):
            return None
        if not recall.get("total_prior_cases"):
            return None

        confirmed = int(recall.get("confirmed_suspicious_count", 0))
        prior_flags = int(recall.get("prior_flag_count", 0))
        prior_reviews = int(recall.get("prior_review_count", 0))
        matched_on = recall.get("matched_on", "account or counterparty")

        severity = 0.0
        reasons: list[str] = []

        if confirmed > 0:
            severity = max(severity, min(75.0, 55.0 + 10.0 * confirmed))
            reasons.append(
                f"{confirmed} prior case(s) for this {matched_on} were confirmed "
                f"suspicious by an analyst."
            )
        if prior_flags > 0:
            severity = max(severity, min(50.0, 35.0 + 5.0 * prior_flags))
            reasons.append(f"{prior_flags} prior case(s) were flagged for filing review.")
        if prior_reviews > 0:
            severity = max(severity, min(30.0, 20.0 + 3.0 * prior_reviews))
            reasons.append(f"{prior_reviews} prior case(s) were routed to analyst review.")

        if severity == 0.0:
            return None

        return self._signal(
            name="adverse_prior_history",
            severity=severity,
            rationale=" ".join(reasons),
            confidence=0.85,
            evidence={key: recall.get(key) for key in sorted(recall)},
            critical=False,
        )
