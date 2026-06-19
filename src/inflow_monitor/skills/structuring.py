"""Structuring (smurfing) detection: inbound deposits kept beneath a threshold."""

from __future__ import annotations

from datetime import timedelta
from typing import Optional

from inflow_monitor.models.case import MonitoringCase, RiskSignal
from inflow_monitor.skills.base import Skill


class StructuringDetectionSkill(Skill):
    """Flags single near-threshold credits and aggregated sub-threshold smurfing.

    Two complementary patterns are evaluated, both classic indicators that funds
    are being broken up to stay below a regulatory reporting threshold:

    1. A single inbound credit that sits just beneath the threshold.
    2. Several sub-threshold credits inside the lookback window that together
       meet or exceed the threshold.
    """

    name = "structuring"

    def evaluate(self, case: MonitoringCase) -> Optional[RiskSignal]:
        settings = self.config.structuring
        event = case.event
        if not event.is_inbound:
            return None

        threshold = settings.reporting_threshold
        near_floor = threshold * settings.near_threshold_ratio

        severity = 0.0
        reasons: list[str] = []
        evidence: dict[str, object] = {}

        # Pattern 1: a single credit parked just below the reporting threshold.
        if near_floor <= event.amount < threshold:
            band = max(threshold - near_floor, 1.0)
            proximity = (event.amount - near_floor) / band
            severity += 40.0 + 20.0 * proximity
            reasons.append(
                f"Inbound credit of {event.amount_label()} sits in the "
                f"{settings.near_threshold_ratio:.0%}-100% band beneath the "
                f"{threshold:,.2f} reporting threshold, consistent with deliberate "
                f"threshold avoidance."
            )
            evidence["near_threshold_amount"] = event.amount
            evidence["reporting_threshold"] = threshold

        # Pattern 2: several sub-threshold credits aggregating above the threshold.
        window_start = event.value_date - timedelta(hours=settings.lookback_hours)
        sub_threshold = [
            prior
            for prior in case.account_history
            if prior.is_inbound
            and prior.account_id == event.account_id
            and window_start <= prior.value_date <= event.value_date
            and prior.amount < threshold
        ]
        count = len(sub_threshold) + 1  # include the event under monitoring
        cumulative = sum(prior.amount for prior in sub_threshold) + event.amount
        if count >= settings.aggregate_count and cumulative >= threshold:
            severity += 35.0
            reasons.append(
                f"{count} sub-threshold inbound credits within "
                f"{settings.lookback_hours}h total {cumulative:,.2f}, meeting or "
                f"exceeding the {threshold:,.2f} threshold in aggregate."
            )
            evidence["sub_threshold_count"] = count
            evidence["cumulative_amount"] = round(cumulative, 2)

        if severity == 0.0:
            return None

        return self._signal(
            name="potential_structuring",
            severity=severity,
            rationale=" ".join(reasons),
            confidence=0.9,
            evidence=evidence,
        )
