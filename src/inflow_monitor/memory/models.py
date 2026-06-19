"""Data models for the collective-memory and feedback layer."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FeedbackLabel(str, Enum):
    """Analyst-confirmed outcome for a previously monitored case."""

    UNREVIEWED = "unreviewed"
    CONFIRMED_SUSPICIOUS = "confirmed_suspicious"
    CLEARED = "cleared"


class CaseMemoryRecord(BaseModel):
    """A persisted record of one monitored case."""

    case_id: str
    account_id: str
    counterparty_id: str
    amount: float
    currency: str
    occurred_at: datetime
    risk_score: float
    outcome: str
    signal_names: list[str] = Field(default_factory=list)
    narrative: str = ""
    label: FeedbackLabel = FeedbackLabel.UNREVIEWED
    label_note: Optional[str] = None
    recorded_at: datetime


class RecallSummary(BaseModel):
    """Aggregated prior history for an account or counterparty."""

    matched_on: str = "none"
    total_prior_cases: int = 0
    confirmed_suspicious_count: int = 0
    cleared_count: int = 0
    prior_flag_count: int = 0
    prior_review_count: int = 0
    most_recent_outcome: Optional[str] = None
    most_recent_at: Optional[datetime] = None

    @property
    def has_history(self) -> bool:
        """Whether any prior cases were found."""
        return self.total_prior_cases > 0

    def as_enrichment(self) -> dict:
        """Render the summary as a plain dict for case enrichment."""
        return {
            "matched_on": self.matched_on,
            "total_prior_cases": self.total_prior_cases,
            "confirmed_suspicious_count": self.confirmed_suspicious_count,
            "cleared_count": self.cleared_count,
            "prior_flag_count": self.prior_flag_count,
            "prior_review_count": self.prior_review_count,
            "most_recent_outcome": self.most_recent_outcome,
            "most_recent_at": (
                self.most_recent_at.isoformat() if self.most_recent_at else None
            ),
        }


class CalibrationReport(BaseModel):
    """Advisory threshold recommendation derived from labeled feedback."""

    labeled_cases: int = 0
    confirmed_suspicious_cases: int = 0
    cleared_cases: int = 0
    current_flag_threshold: float = 0.0
    current_review_threshold: float = 0.0
    suggested_flag_threshold: Optional[float] = None
    suggested_review_threshold: Optional[float] = None
    rationale: list[str] = Field(default_factory=list)
