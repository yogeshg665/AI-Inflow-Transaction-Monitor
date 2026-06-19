---
name: source-screening
description: Screens the origin of inbound funds against sanctions, watchlists, and high-risk jurisdictions, raising a definitive critical signal for sanctioned sources. WHEN: "screen the source of funds", "is the sender sanctioned", "watchlist check on counterparty", "high-risk country inflow", "sanctions screening on a credit".
---

# Source Screening

## Overview

Screens the originator and source country of an inbound credit. A sanctioned
source is a definitive (critical) hit that sets a floor on the score; a
watchlisted counterparty or high-risk origin country raise the signal without
being definitive alone.

## When to Use

- During detection, for every inbound credit.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `event.source_country` | yes | ISO country the funds originated from. |
| `event.counterparty_id` | yes | Pseudonymous originator identifier. |
| `enrichment.source_sanctioned` | no | Boolean sanctions flag from screening. |
| `enrichment.counterparty_watchlist` | no | List of watchlisted counterparty ids. |

## Process

1. If the source is flagged sanctioned, raise a critical signal at high severity.
2. If the counterparty is on the supplied watchlist, raise severity.
3. If the source country is high risk, raise severity.
4. Emit a `high_risk_source` signal, marked critical only for a sanctions hit.

## Outputs

Zero or one `RiskSignal` named `high_risk_source`; `critical` when sanctioned.

## Reference Implementation

`src/inflow_monitor/skills/source_screening.py`.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "A sanctions hit can be averaged down." | It is critical and sets a score floor; it cannot be diluted. |
| "High-risk country alone should block." | It contributes severity; the policy decides the outcome. |

## Red Flags

- A sanctions hit is emitted as non-critical.
- Screening reaches external services in the deterministic engine instead of
  reading enrichment.

## Verification

- A sanctioned source yields a critical signal; the aggregate score reflects the
  floor it sets.
