"""Registry that assembles the default detector set from configuration."""

from __future__ import annotations

from inflow_monitor.skills.base import Skill
from inflow_monitor.skills.credit_anomaly import CreditAnomalySkill
from inflow_monitor.skills.cross_border import CrossBorderRiskSkill
from inflow_monitor.skills.inflow_velocity import InflowVelocitySkill
from inflow_monitor.skills.mule_activity import MuleActivitySkill
from inflow_monitor.skills.prior_history import PriorHistorySkill
from inflow_monitor.skills.source_screening import SourceScreeningSkill
from inflow_monitor.skills.structuring import StructuringDetectionSkill
from inflow_monitor.utils.config import EngineConfig

_SKILL_TYPES: list[type[Skill]] = [
    StructuringDetectionSkill,
    MuleActivitySkill,
    CreditAnomalySkill,
    SourceScreeningSkill,
    InflowVelocitySkill,
    CrossBorderRiskSkill,
    PriorHistorySkill,
]


def default_skills(config: EngineConfig) -> list[Skill]:
    """Instantiate the standard detector set bound to the given configuration."""
    return [skill_type(config) for skill_type in _SKILL_TYPES]
