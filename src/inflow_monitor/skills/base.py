"""Base class shared by all inflow detection skills."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from inflow_monitor.models.case import MonitoringCase, RiskSignal
from inflow_monitor.utils.config import EngineConfig


class Skill(ABC):
    """Abstract base for a single inflow detector.

    Subclasses implement :meth:`evaluate` and return a :class:`RiskSignal` when
    the check fires, or ``None`` when there is nothing to report. Detectors must
    be deterministic and side-effect free so monitoring stays reproducible.
    """

    #: Stable identifier used for configuration, weighting, and reporting.
    name: str = "skill"

    def __init__(self, config: EngineConfig) -> None:
        self.config = config

    @abstractmethod
    def evaluate(self, case: MonitoringCase) -> Optional[RiskSignal]:
        """Inspect the case and optionally emit a risk signal."""
        raise NotImplementedError

    def _signal(
        self,
        name: str,
        severity: float,
        rationale: str,
        confidence: float = 1.0,
        evidence: dict | None = None,
        critical: bool = False,
    ) -> RiskSignal:
        """Helper to build a well-formed risk signal for this detector."""
        return RiskSignal(
            skill=self.name,
            name=name,
            severity=max(0.0, min(100.0, severity)),
            confidence=confidence,
            rationale=rationale,
            critical=critical,
            evidence=evidence or {},
        )
