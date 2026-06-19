"""Base agent definition."""

from __future__ import annotations

from abc import ABC

from inflow_monitor.utils.config import EngineConfig
from inflow_monitor.utils.logging import get_logger


class Agent(ABC):
    """Common base for all monitoring agents.

    Agents are stateless with respect to individual cases; all case state is
    carried on the :class:`MonitoringCase` passed between stages. This keeps the
    pipeline horizontally scalable and easy to reason about.
    """

    #: Human-readable agent name used in logs and reports.
    name: str = "agent"

    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self.logger = get_logger(f"agent.{self.name}")
