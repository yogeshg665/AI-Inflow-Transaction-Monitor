"""Typed configuration model and loader for the monitoring engine."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class DecisionPolicy(BaseModel):
    # Risk score (0-100) at or above which an inbound transaction is flagged.
    flag_threshold: float = 75.0
    # Risk score (0-100) at or above which a case is routed for analyst review.
    review_threshold: float = 45.0


class EngineSettings(BaseModel):
    max_batch_size: int = 1000
    persist_reports: bool = True


class StructuringConfig(BaseModel):
    # Regulatory reporting threshold the deposits are being kept beneath.
    reporting_threshold: float = 10000.0
    # Fraction of the threshold above which a single credit is "near-threshold".
    near_threshold_ratio: float = 0.9
    # Window for aggregating multiple sub-threshold credits.
    lookback_hours: int = 72
    # Number of sub-threshold credits in the window that implies smurfing.
    aggregate_count: int = 3


class MuleActivityConfig(BaseModel):
    # Window after the credit within which outbound drains are pass-through.
    passthrough_window_hours: int = 24
    # Fraction of the credit moved out that implies pass-through behavior.
    passthrough_ratio: float = 0.8
    # Minimum inbound amount before pass-through is evaluated.
    min_inbound_amount: float = 1000.0


class CreditAnomalyConfig(BaseModel):
    # Z-score above which an inbound amount is a statistical outlier.
    zscore_threshold: float = 3.0
    # Multiple of the historical mean inbound that is treated as anomalous.
    baseline_multiple: float = 5.0
    # Minimum number of prior inbound movements required to form a baseline.
    min_history: int = 3


class SourceScreeningConfig(BaseModel):
    # Country codes whose inbound funds warrant additional scrutiny.
    high_risk_countries: list[str] = Field(default_factory=list)


class InflowVelocityConfig(BaseModel):
    # Window used to count recent inbound credits for the same account.
    window_hours: int = 24
    # Inbound count within the window considered a burst.
    max_inbound_count: int = 4
    # Cumulative inbound amount within the window considered a burst.
    max_inbound_amount: float = 15000.0


class CrossBorderConfig(BaseModel):
    # Expected home currency for the account; mismatches add risk.
    home_currency: str = "USD"
    # Country codes that elevate a cross-border corridor.
    high_risk_countries: list[str] = Field(default_factory=list)


class MemoryConfig(BaseModel):
    # When enabled, monitored cases are persisted and prior history is recalled.
    enabled: bool = False
    # Filesystem path to the SQLite memory database.
    path: str = ".inflow_memory/memory.db"


class EngineConfig(BaseModel):
    """Aggregate, strongly typed engine configuration."""

    engine: EngineSettings = Field(default_factory=EngineSettings)
    decision_policy: DecisionPolicy = Field(default_factory=DecisionPolicy)
    skill_weights: dict[str, float] = Field(default_factory=dict)
    structuring: StructuringConfig = Field(default_factory=StructuringConfig)
    mule_activity: MuleActivityConfig = Field(default_factory=MuleActivityConfig)
    credit_anomaly: CreditAnomalyConfig = Field(default_factory=CreditAnomalyConfig)
    source_screening: SourceScreeningConfig = Field(default_factory=SourceScreeningConfig)
    inflow_velocity: InflowVelocityConfig = Field(default_factory=InflowVelocityConfig)
    cross_border: CrossBorderConfig = Field(default_factory=CrossBorderConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)

    def _apply_env_overrides(self) -> None:
        """Allow critical thresholds to be overridden via environment variables."""
        flag = os.getenv("RISK_FLAG_THRESHOLD")
        review = os.getenv("RISK_REVIEW_THRESHOLD")
        if flag is not None:
            self.decision_policy.flag_threshold = float(flag)
        if review is not None:
            self.decision_policy.review_threshold = float(review)
        memory_enabled = os.getenv("MEMORY_ENABLED")
        memory_path = os.getenv("MEMORY_PATH")
        if memory_enabled is not None:
            self.memory.enabled = memory_enabled.strip().lower() in {"1", "true", "yes", "on"}
        if memory_path is not None:
            self.memory.path = memory_path


def _default_config_path() -> Path:
    return Path(__file__).resolve().parents[3] / "config" / "config.yaml"


def load_config(path: str | Path | None = None) -> EngineConfig:
    """Load engine configuration from YAML, applying environment overrides.

    Falls back to built-in defaults when no configuration file is present.
    """
    config_path = Path(path) if path else _default_config_path()
    data: dict[str, Any] = {}
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}

    config = EngineConfig(**data)
    config._apply_env_overrides()
    return config
