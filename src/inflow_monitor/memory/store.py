"""SQLite-backed collective memory for monitored cases.

The store persists completed cases using only pseudonymous account and
counterparty identifiers, recalls prior history for a given inbound event, and
records analyst feedback. It uses the standard-library ``sqlite3`` module so no
additional dependency is required. All operations are deterministic.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from inflow_monitor.memory.models import (
    CaseMemoryRecord,
    FeedbackLabel,
    RecallSummary,
)
from inflow_monitor.models.case import MonitoringCase
from inflow_monitor.models.decision import Decision
from inflow_monitor.models.movement import MovementEvent
from inflow_monitor.utils.logging import get_logger

logger = get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS case_memory (
    case_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    counterparty_id TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    risk_score REAL NOT NULL,
    outcome TEXT NOT NULL,
    signal_names TEXT NOT NULL,
    narrative TEXT NOT NULL,
    label TEXT NOT NULL,
    label_note TEXT,
    recorded_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_case_memory_account ON case_memory(account_id);
CREATE INDEX IF NOT EXISTS idx_case_memory_counterparty ON case_memory(counterparty_id);
"""


class MemoryStore:
    """A small, deterministic case memory backed by SQLite."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # -- persistence -------------------------------------------------------

    def record_investigation(
        self, case: MonitoringCase, decision: Decision
    ) -> CaseMemoryRecord:
        """Persist a completed monitored case, preserving any existing label."""
        event = case.event
        existing = self._get(case.case_id)
        record = CaseMemoryRecord(
            case_id=case.case_id,
            account_id=event.account_id,
            counterparty_id=event.counterparty_id,
            amount=event.amount,
            currency=event.currency,
            occurred_at=event.value_date,
            risk_score=case.risk_score,
            outcome=decision.outcome.value,
            signal_names=[signal.name for signal in case.triggered_signals()],
            narrative=decision.narrative,
            label=existing.label if existing else FeedbackLabel.UNREVIEWED,
            label_note=existing.label_note if existing else None,
            recorded_at=datetime.now(timezone.utc),
        )
        self._upsert(record)
        return record

    def _upsert(self, record: CaseMemoryRecord) -> None:
        self._conn.execute(
            """
            INSERT INTO case_memory (
                case_id, account_id, counterparty_id, amount, currency,
                occurred_at, risk_score, outcome, signal_names, narrative,
                label, label_note, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(case_id) DO UPDATE SET
                account_id=excluded.account_id,
                counterparty_id=excluded.counterparty_id,
                amount=excluded.amount,
                currency=excluded.currency,
                occurred_at=excluded.occurred_at,
                risk_score=excluded.risk_score,
                outcome=excluded.outcome,
                signal_names=excluded.signal_names,
                narrative=excluded.narrative,
                label=excluded.label,
                label_note=excluded.label_note,
                recorded_at=excluded.recorded_at
            """,
            (
                record.case_id,
                record.account_id,
                record.counterparty_id,
                record.amount,
                record.currency,
                record.occurred_at.isoformat(),
                record.risk_score,
                record.outcome,
                "|".join(record.signal_names),
                record.narrative,
                record.label.value,
                record.label_note,
                record.recorded_at.isoformat(),
            ),
        )
        self._conn.commit()

    # -- recall ------------------------------------------------------------

    def recall_similar(self, event: MovementEvent) -> RecallSummary:
        """Summarize prior cases for the same account or counterparty.

        The currently monitored case (if already persisted) is excluded so a
        re-run does not recall itself.
        """
        marker = self._case_marker(event)
        rows = self._conn.execute(
            """
            SELECT * FROM case_memory
            WHERE (account_id = ? OR counterparty_id = ?)
              AND case_id != ?
            ORDER BY occurred_at DESC, case_id ASC
            """,
            (event.account_id, event.counterparty_id, marker),
        ).fetchall()
        if not rows:
            return RecallSummary()

        matched_account = any(row["account_id"] == event.account_id for row in rows)
        matched_counterparty = any(
            row["counterparty_id"] == event.counterparty_id for row in rows
        )
        if matched_account and matched_counterparty:
            matched_on = "account and counterparty"
        elif matched_account:
            matched_on = "account"
        else:
            matched_on = "counterparty"

        confirmed = sum(
            1 for row in rows if row["label"] == FeedbackLabel.CONFIRMED_SUSPICIOUS.value
        )
        cleared = sum(1 for row in rows if row["label"] == FeedbackLabel.CLEARED.value)
        prior_flags = sum(1 for row in rows if row["outcome"] == "flag")
        prior_reviews = sum(1 for row in rows if row["outcome"] == "review")

        most_recent = rows[0]
        return RecallSummary(
            matched_on=matched_on,
            total_prior_cases=len(rows),
            confirmed_suspicious_count=confirmed,
            cleared_count=cleared,
            prior_flag_count=prior_flags,
            prior_review_count=prior_reviews,
            most_recent_outcome=most_recent["outcome"],
            most_recent_at=self._parse_dt(most_recent["occurred_at"]),
        )

    # -- feedback ----------------------------------------------------------

    def record_feedback(
        self, case_id: str, label: FeedbackLabel, note: str | None = None
    ) -> bool:
        """Attach an analyst label to a stored case. Returns False if unknown."""
        cursor = self._conn.execute(
            "UPDATE case_memory SET label = ?, label_note = ? WHERE case_id = ?",
            (label.value, note, case_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    # -- queries -----------------------------------------------------------

    def all_records(self) -> list[CaseMemoryRecord]:
        """Return every stored case as a model."""
        rows = self._conn.execute(
            "SELECT * FROM case_memory ORDER BY occurred_at ASC, case_id ASC"
        ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def stats(self) -> dict:
        """Return simple counts for diagnostics."""
        rows = self._conn.execute("SELECT label, COUNT(*) AS n FROM case_memory GROUP BY label")
        by_label = {row["label"]: row["n"] for row in rows}
        total = sum(by_label.values())
        return {"total": total, "by_label": by_label}

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "MemoryStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # -- helpers -----------------------------------------------------------

    def _get(self, case_id: str) -> Optional[CaseMemoryRecord]:
        row = self._conn.execute(
            "SELECT * FROM case_memory WHERE case_id = ?", (case_id,)
        ).fetchone()
        return self._row_to_record(row) if row else None

    @staticmethod
    def _case_marker(event: MovementEvent) -> str:
        """A stable marker used only to exclude an event's own pending case."""
        return f"pending::{event.event_id}"

    @staticmethod
    def _parse_dt(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _row_to_record(self, row: sqlite3.Row) -> CaseMemoryRecord:
        names = [name for name in (row["signal_names"] or "").split("|") if name]
        return CaseMemoryRecord(
            case_id=row["case_id"],
            account_id=row["account_id"],
            counterparty_id=row["counterparty_id"],
            amount=row["amount"],
            currency=row["currency"],
            occurred_at=self._parse_dt(row["occurred_at"]),
            risk_score=row["risk_score"],
            outcome=row["outcome"],
            signal_names=names,
            narrative=row["narrative"],
            label=FeedbackLabel(row["label"]),
            label_note=row["label_note"],
            recorded_at=self._parse_dt(row["recorded_at"]),
        )
