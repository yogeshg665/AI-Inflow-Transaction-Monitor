"""Intake agent: validates input and constructs the monitoring case."""

from __future__ import annotations

import uuid

from inflow_monitor.agents.base import Agent
from inflow_monitor.models.case import MonitoringCase
from inflow_monitor.models.movement import MovementEvent


class IntakeAgent(Agent):
    """Normalizes raw input into a validated :class:`MonitoringCase`."""

    name = "intake"

    def run(
        self,
        event: MovementEvent,
        account_history: list[MovementEvent] | None = None,
    ) -> MonitoringCase:
        """Create a case from an inbound event and optional account history."""
        history = account_history or []
        case = MonitoringCase(
            case_id=f"case_{uuid.uuid4().hex[:12]}",
            event=event,
            account_history=sorted(history, key=lambda item: item.value_date),
        )
        self.logger.info(
            "Opened %s for inbound event %s on account %s",
            case.case_id,
            event.event_id,
            event.account_id,
        )
        return case
