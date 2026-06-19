"""Cross-border risk: foreign-origin inflows and currency mismatches."""

from __future__ import annotations

from typing import Optional

from inflow_monitor.models.case import MonitoringCase, RiskSignal
from inflow_monitor.skills.base import Skill


class CrossBorderRiskSkill(Skill):
    """Flags cross-border inflows and currency mismatches against the home setup.

    Cross-border corridors and currency mismatches do not imply wrongdoing on
    their own, but they materially raise laundering risk and are weighted
    accordingly. A high-risk origin corridor adds further severity.
    """

    name = "cross_border"

    def evaluate(self, case: MonitoringCase) -> Optional[RiskSignal]:
        settings = self.config.cross_border
        event = case.event
        if not event.is_inbound:
            return None

        severity = 0.0
        reasons: list[str] = []
        evidence: dict[str, object] = {}

        if event.source_country != event.account_country:
            severity += 30.0
            reasons.append(
                f"Cross-border inflow from {event.source_country} into an account "
                f"booked in {event.account_country}."
            )
            evidence["source_country"] = event.source_country
            evidence["account_country"] = event.account_country

            if event.source_country in settings.high_risk_countries:
                severity += 20.0
                reasons.append(
                    f"Origin {event.source_country} is a high-risk corridor for this "
                    f"account."
                )
                evidence["high_risk_corridor"] = True

        if event.currency.upper() != settings.home_currency.upper():
            severity += 20.0
            reasons.append(
                f"Credit is denominated in {event.currency}, a mismatch with the "
                f"account home currency {settings.home_currency}."
            )
            evidence["currency"] = event.currency
            evidence["home_currency"] = settings.home_currency

        if severity == 0.0:
            return None

        return self._signal(
            name="cross_border_inflow",
            severity=severity,
            rationale=" ".join(reasons),
            confidence=0.8,
            evidence=evidence,
        )
