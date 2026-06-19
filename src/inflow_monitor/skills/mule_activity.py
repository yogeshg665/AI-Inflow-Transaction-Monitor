"""Mule-account detection: rapid inbound-then-outbound pass-through of funds."""

from __future__ import annotations

from datetime import timedelta
from typing import Optional

from inflow_monitor.models.case import MonitoringCase, RiskSignal
from inflow_monitor.skills.base import Skill


class MuleActivitySkill(Skill):
    """Flags credits that are quickly drained out again (pass-through behavior).

    A hallmark of mule accounts is that inbound funds do not rest: a large credit
    arrives and a high fraction is moved out within a short window. The detector
    measures the outbound drain that follows the monitored credit and scores the
    pass-through ratio.
    """

    name = "mule_activity"

    def evaluate(self, case: MonitoringCase) -> Optional[RiskSignal]:
        settings = self.config.mule_activity
        event = case.event
        if not event.is_inbound or event.amount < settings.min_inbound_amount:
            return None

        window_end = event.value_date + timedelta(hours=settings.passthrough_window_hours)
        outbound = [
            prior
            for prior in case.account_history
            if not prior.is_inbound
            and prior.account_id == event.account_id
            and event.value_date <= prior.value_date <= window_end
        ]
        if not outbound:
            return None

        drained = sum(item.amount for item in outbound)
        ratio = drained / max(event.amount, 1.0)
        if ratio < settings.passthrough_ratio:
            return None

        capped_ratio = min(ratio, 1.5)
        severity = 50.0 + 30.0 * min(1.0, capped_ratio)
        rationale = (
            f"{capped_ratio:.0%} of the {event.amount_label()} credit "
            f"({drained:,.2f}) was moved out across {len(outbound)} outbound "
            f"movement(s) within {settings.passthrough_window_hours}h, consistent "
            f"with mule-account pass-through where funds do not rest."
        )
        return self._signal(
            name="rapid_passthrough",
            severity=severity,
            rationale=rationale,
            confidence=0.85,
            evidence={
                "credited_amount": round(event.amount, 2),
                "drained_amount": round(drained, 2),
                "passthrough_ratio": round(ratio, 2),
                "outbound_count": len(outbound),
                "window_hours": settings.passthrough_window_hours,
            },
        )
