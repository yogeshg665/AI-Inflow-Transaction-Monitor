---
name: counterparty-enrichment
description: Adds derived baseline and reference context to a monitoring case, including the account inbound baseline, whether the counterparty was seen before, and a cross-border flag. WHEN: "enrich this case", "add counterparty context", "compute the inbound baseline", "is this counterparty known", "add reference data before detection".
---

# Counterparty Enrichment

## Overview

Computes contextual features the detectors rely on, deterministically from the
provided account history, and merges any caller-supplied enrichment such as
sanctions or watchlist flags.

## When to Use

- Immediately after intake and before detection.
- Do NOT use it to emit risk signals; it only prepares context.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `case.event` | yes | The inbound event under monitoring. |
| `case.account_history` | no | Prior movements used to derive a baseline. |
| `case.enrichment` | no | Caller-supplied flags (for example `source_sanctioned`). |

## Process

1. Compute the inbound baseline (count, mean, standard deviation) from history.
2. Determine whether the counterparty has been seen on this account before.
3. Set a `cross_border` flag from the source and account countries.
4. Merge caller-supplied enrichment last so it takes precedence.

## Outputs

An updated `case.enrichment` map consumed by downstream detectors.

## Reference Implementation

`src/inflow_monitor/agents/enrichment_agent.py`.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "Derived values should override caller data." | Caller-supplied reference data is authoritative; it wins. |
| "Baseline needs no minimum history." | Detectors enforce their own minimums; provide what exists. |

## Red Flags

- Enrichment performs external network calls in the deterministic engine.
- Caller-supplied sanctions flags are silently dropped.

## Verification

- `case.enrichment` contains the derived features and any caller-supplied flags.
