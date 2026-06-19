"""Optional collective-memory, recall, and feedback layer.

This subsystem is disabled by default. When enabled it persists monitored cases,
recalls prior history for repeat accounts or counterparties, accepts analyst
feedback labels, and recommends thresholds from those labels. All recall and
calibration is deterministic; the memory signal is never critical and
calibration is advisory only.
"""

from inflow_monitor.memory.calibration import calibrate_thresholds
from inflow_monitor.memory.models import (
    CalibrationReport,
    CaseMemoryRecord,
    FeedbackLabel,
    RecallSummary,
)
from inflow_monitor.memory.store import MemoryStore

__all__ = [
    "MemoryStore",
    "CaseMemoryRecord",
    "RecallSummary",
    "CalibrationReport",
    "FeedbackLabel",
    "calibrate_thresholds",
]
