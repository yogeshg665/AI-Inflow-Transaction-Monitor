"""Credit-anomaly detection: inbound amounts that deviate from the baseline."""

from __future__ import annotations

import statistics
from typing import Optional

from inflow_monitor.models.case import MonitoringCase, RiskSignal
from inflow_monitor.skills.base import Skill


class CreditAnomalySkill(Skill):
    """Flags inbound credits that are statistical outliers versus account history.

    The detector builds a baseline from the account's prior inbound amounts and
    scores the monitored credit two ways: a z-score relative to the historical
    distribution, and a simple multiple of the historical mean. Either path can
    raise the signal so that thin or wide distributions are both handled.
    """

    name = "credit_anomaly"

    def evaluate(self, case: MonitoringCase) -> Optional[RiskSignal]:
        settings = self.config.credit_anomaly
        event = case.event
        if not event.is_inbound:
            return None

        history = [
            prior.amount
            for prior in case.account_history
            if prior.is_inbound and prior.account_id == event.account_id
        ]
        if len(history) < settings.min_history:
            return None

        mean = statistics.fmean(history)
        stdev = statistics.pstdev(history)

        severity = 0.0
        reasons: list[str] = []
        evidence: dict[str, object] = {
            "history_count": len(history),
            "baseline_mean": round(mean, 2),
        }

        if stdev > 0.0:
            zscore = (event.amount - mean) / stdev
            if zscore >= settings.zscore_threshold:
                severity += min(60.0, 20.0 * (zscore - settings.zscore_threshold) + 40.0)
                reasons.append(
                    f"Inbound amount {event.amount_label()} is {zscore:.1f} standard "
                    f"deviations above the account's mean inbound of {mean:,.2f}."
                )
                evidence["zscore"] = round(zscore, 2)

        if mean > 0.0 and event.amount >= mean * settings.baseline_multiple:
            multiple = event.amount / mean
            severity += 30.0
            reasons.append(
                f"Inbound amount is {multiple:.1f}x the historical mean inbound of "
                f"{mean:,.2f}, far outside normal account behavior."
            )
            evidence["baseline_multiple"] = round(multiple, 2)

        if severity == 0.0:
            return None

        return self._signal(
            name="anomalous_credit",
            severity=severity,
            rationale=" ".join(reasons),
            confidence=0.8,
            evidence=evidence,
        )
