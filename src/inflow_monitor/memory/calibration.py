"""Advisory threshold calibration from labeled feedback.

Calibration is deterministic and advisory only. It never mutates configuration;
it merely recommends thresholds that would have separated analyst-confirmed
suspicious cases from cleared cases, given their recorded risk scores.
"""

from __future__ import annotations

from inflow_monitor.memory.models import (
    CalibrationReport,
    CaseMemoryRecord,
    FeedbackLabel,
)
from inflow_monitor.utils.config import DecisionPolicy


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def calibrate_thresholds(
    records: list[CaseMemoryRecord], policy: DecisionPolicy
) -> CalibrationReport:
    """Recommend flag and review thresholds from labeled case scores."""
    suspicious = [
        record.risk_score
        for record in records
        if record.label is FeedbackLabel.CONFIRMED_SUSPICIOUS
    ]
    cleared = [
        record.risk_score for record in records if record.label is FeedbackLabel.CLEARED
    ]

    report = CalibrationReport(
        labeled_cases=len(suspicious) + len(cleared),
        confirmed_suspicious_cases=len(suspicious),
        cleared_cases=len(cleared),
        current_flag_threshold=policy.flag_threshold,
        current_review_threshold=policy.review_threshold,
    )

    if not suspicious or not cleared:
        report.rationale.append(
            "At least one confirmed-suspicious and one cleared case are required to "
            "recommend thresholds. No change suggested."
        )
        return report

    lowest_suspicious = min(suspicious)
    highest_cleared = max(cleared)

    if lowest_suspicious > highest_cleared:
        # Cleanly separable: place the flag threshold at the midpoint.
        flag = (lowest_suspicious + highest_cleared) / 2
        report.rationale.append(
            f"Labels are separable: cleared scores top out at {highest_cleared:.1f} "
            f"and confirmed-suspicious scores start at {lowest_suspicious:.1f}. "
            f"Suggested flag threshold is their midpoint."
        )
    else:
        # Overlapping: bias toward catching suspicious activity.
        flag = max(lowest_suspicious, highest_cleared)
        report.rationale.append(
            f"Labels overlap between {highest_cleared:.1f} (cleared) and "
            f"{lowest_suspicious:.1f} (suspicious). Suggested flag threshold favors "
            f"recall of suspicious activity."
        )

    review = min(flag, highest_cleared)
    report.suggested_flag_threshold = round(_clamp(flag), 1)
    report.suggested_review_threshold = round(_clamp(review), 1)
    report.rationale.append(
        "Recommendation is advisory only; thresholds in configuration are unchanged."
    )
    return report
