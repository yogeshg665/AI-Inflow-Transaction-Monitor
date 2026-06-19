---
name: structuring-detection
description: Detects structuring (smurfing) where inbound funds are kept beneath a regulatory reporting threshold, either as a single near-threshold credit or as several sub-threshold credits that aggregate above it. WHEN: "check for structuring", "is this deposit near the reporting threshold", "smurfing detection", "are these credits being broken up", "sub-threshold deposit pattern".
---

# Structuring Detection

## Overview

Flags two classic threshold-avoidance patterns: a single inbound credit parked
just beneath the reporting threshold, and multiple sub-threshold credits within
the lookback window that together meet or exceed it.

## When to Use

- During the detection phase of every monitored inbound credit.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `event.amount` | yes | Inbound credit amount. |
| `account_history` | no | Prior inbound credits used for aggregation. |

## Process

1. If the amount sits in the configured near-threshold band, add severity scaled
   by proximity to the threshold.
2. Count sub-threshold inbound credits in the lookback window, including this
   one, and sum them.
3. If the count meets the aggregate trigger and the sum meets or exceeds the
   threshold, add severity.
4. Emit a `potential_structuring` signal with a rationale, or nothing.

## Outputs

Zero or one `RiskSignal` named `potential_structuring`.

## Reference Implementation

`src/inflow_monitor/skills/structuring.py`.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "A single near-threshold deposit is coincidence." | It contributes risk; scoring weighs it alongside other signals. |
| "Aggregation needs exact equality to the threshold." | Meeting or exceeding in aggregate is the trigger, not equality. |

## Red Flags

- Severity is emitted without naming the threshold and amounts in the rationale.
- The reporting threshold is hardcoded instead of read from configuration.

## Verification

- A near-threshold or aggregated pattern yields a signal with a clear rationale.
