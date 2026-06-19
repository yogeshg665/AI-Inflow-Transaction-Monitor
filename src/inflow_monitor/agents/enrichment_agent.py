"""Enrichment agent: augments the case with derived context features.

In production, enrichment would call external reference services (sanctions and
watchlist providers, counterparty intelligence). This implementation derives
features deterministically from the provided account history and merges any
enrichment supplied with the input, so the engine runs without external
dependencies while preserving the same downstream contract.
"""

from __future__ import annotations

import statistics

from inflow_monitor.agents.base import Agent
from inflow_monitor.models.case import MonitoringCase


class EnrichmentAgent(Agent):
    """Computes contextual features used by downstream detectors."""

    name = "enrichment"

    def run(self, case: MonitoringCase) -> MonitoringCase:
        event = case.event
        derived: dict[str, object] = {}

        inbound_history = [
            prior.amount
            for prior in case.account_history
            if prior.is_inbound and prior.account_id == event.account_id
        ]
        if inbound_history:
            derived["inbound_baseline"] = {
                "count": len(inbound_history),
                "mean": round(statistics.fmean(inbound_history), 2),
                "stdev": round(statistics.pstdev(inbound_history), 2),
            }

        counterparties_seen = {
            prior.counterparty_id
            for prior in case.account_history
            if prior.account_id == event.account_id
        }
        derived["counterparty_seen_before"] = event.counterparty_id in counterparties_seen
        derived["cross_border"] = event.source_country != event.account_country

        # Caller-supplied enrichment takes precedence over derived values.
        merged = {**derived, **case.enrichment}
        case.enrichment = merged
        self.logger.info("Enriched %s with %d feature(s)", case.case_id, len(merged))
        return case
