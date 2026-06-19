"""Source screening: high-risk geography, watchlists, and sanctioned origins."""

from __future__ import annotations

from typing import Optional

from inflow_monitor.models.case import MonitoringCase, RiskSignal
from inflow_monitor.skills.base import Skill


class SourceScreeningSkill(Skill):
    """Screens the origin of inbound funds against risk and sanctions context.

    Three escalating conditions are evaluated. A sanctioned source is a
    definitive (critical) indicator and sets a floor on the aggregate score; a
    watchlisted counterparty or a high-risk origin country raise the signal
    without being definitive on their own.

    Sanctions and watchlist context is supplied via case enrichment so the
    detector remains deterministic and free of external calls. Recognized keys:
    ``source_sanctioned`` (bool) and ``counterparty_watchlist`` (list of ids).
    """

    name = "source_screening"

    def evaluate(self, case: MonitoringCase) -> Optional[RiskSignal]:
        settings = self.config.source_screening
        event = case.event
        if not event.is_inbound:
            return None

        enrichment = case.enrichment
        watchlist = {str(item) for item in enrichment.get("counterparty_watchlist", [])}

        severity = 0.0
        critical = False
        reasons: list[str] = []
        evidence: dict[str, object] = {
            "source_country": event.source_country,
            "counterparty_id": event.counterparty_id,
        }

        if bool(enrichment.get("source_sanctioned")):
            severity = max(severity, 90.0)
            critical = True
            reasons.append(
                f"Inbound funds originate from a sanctioned source "
                f"({event.counterparty_id}); this is a definitive screening hit."
            )
            evidence["source_sanctioned"] = True

        if event.counterparty_id in watchlist:
            severity = max(severity, 70.0)
            reasons.append(
                f"Originating counterparty {event.counterparty_id} appears on the "
                f"provided watchlist."
            )
            evidence["watchlist_hit"] = True

        if event.source_country in settings.high_risk_countries:
            severity = max(severity, 55.0)
            reasons.append(
                f"Funds originate from high-risk jurisdiction "
                f"{event.source_country}."
            )
            evidence["high_risk_country"] = event.source_country

        if severity == 0.0:
            return None

        return self._signal(
            name="high_risk_source",
            severity=severity,
            rationale=" ".join(reasons),
            confidence=0.95 if critical else 0.85,
            evidence=evidence,
            critical=critical,
        )
