"""Detection swarm: runs the detector skills as a coordinated agent group.

The swarm executes every detector independently, isolates failures so one
detector cannot abort the case, and records a per-detector contribution summary
on the case enrichment. The swarm only produces signals; aggregation into a
single score is the responsibility of the risk-scoring agent. This separation
keeps detection composable and the score deterministic.
"""

from __future__ import annotations

from inflow_monitor.agents.base import Agent
from inflow_monitor.models.case import MonitoringCase
from inflow_monitor.skills.base import Skill
from inflow_monitor.skills.registry import default_skills


class DetectionSwarmAgent(Agent):
    """Coordinates the detector skills and collects their signals."""

    name = "detection_swarm"

    def __init__(self, config, skills: list[Skill] | None = None) -> None:
        super().__init__(config)
        self.skills = skills if skills is not None else default_skills(config)

    def run(self, case: MonitoringCase) -> MonitoringCase:
        contributions: list[dict[str, object]] = []
        for skill in self.skills:
            try:
                signal = skill.evaluate(case)
            except Exception:  # pragma: no cover - defensive isolation per detector
                self.logger.exception("Detector '%s' raised an error; skipping", skill.name)
                continue
            if signal is not None and signal.triggered:
                case.add_signal(signal)
                contributions.append(
                    {
                        "detector": signal.skill,
                        "signal": signal.name,
                        "severity": signal.severity,
                        "confidence": signal.confidence,
                        "critical": signal.critical,
                    }
                )

        case.enrichment["swarm_contributions"] = contributions
        self.logger.info(
            "Detection swarm produced %d signal(s) for %s",
            len(contributions),
            case.case_id,
        )
        return case
