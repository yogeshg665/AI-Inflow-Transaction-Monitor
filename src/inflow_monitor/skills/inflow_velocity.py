"""Inflow velocity: bursts of inbound credits within a short window."""

from __future__ import annotations

from datetime import timedelta
from typing import Optional

from inflow_monitor.models.case import MonitoringCase, RiskSignal
from inflow_monitor.skills.base import Skill


class InflowVelocitySkill(Skill):
    """Detects an abnormal count or sum of inbound credits in a short window.

    Rapid sequencing of inbound credits is a common funnel pattern: many sources
    pushing funds into one account over a short period. The detector counts and
    sums inbound movements inside the configured window, including the monitored
    credit, and raises severity when either limit is exceeded.
    """

    name = "inflow_velocity"

    def evaluate(self, case: MonitoringCase) -> Optional[RiskSignal]:
        settings = self.config.inflow_velocity
        event = case.event
        if not event.is_inbound:
            return None

        window_start = event.value_date - timedelta(hours=settings.window_hours)
        recent = [
            prior
            for prior in case.account_history
            if prior.is_inbound
            and prior.account_id == event.account_id
            and window_start <= prior.value_date <= event.value_date
        ]
        count = len(recent) + 1  # include the monitored credit
        total = sum(prior.amount for prior in recent) + event.amount

        severity = 0.0
        reasons: list[str] = []

        if count > settings.max_inbound_count:
            severity += min(60.0, 15.0 * (count - settings.max_inbound_count) + 30.0)
            reasons.append(
                f"{count} inbound credits within {settings.window_hours}h exceeds the "
                f"limit of {settings.max_inbound_count}."
            )

        if total > settings.max_inbound_amount:
            severity += 40.0
            reasons.append(
                f"Cumulative inbound {total:,.2f} within the window exceeds the limit "
                f"of {settings.max_inbound_amount:,.2f}."
            )

        if severity == 0.0:
            return None

        return self._signal(
            name="inbound_velocity_burst",
            severity=severity,
            rationale=" ".join(reasons),
            confidence=0.85,
            evidence={
                "inbound_count": count,
                "window_hours": settings.window_hours,
                "cumulative_inbound": round(total, 2),
            },
        )
