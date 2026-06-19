---
name: inflow-velocity
description: Detects bursts of inbound credits, raising a signal when the count or cumulative amount of inbound movements within a short window exceeds configured limits. WHEN: "check inflow velocity", "burst of incoming credits", "many deposits in a short time", "funnel pattern of inbound funds", "rapid sequence of credits".
---

# Inflow Velocity

## Overview

Detects rapid sequencing of inbound credits, a common funnel pattern where many
sources push funds into one account over a short period. It counts and sums
inbound movements inside the window, including the monitored credit.

## When to Use

- During detection, for every inbound credit.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `event.value_date` | yes | Settlement time used to define the window. |
| `account_history` | no | Prior inbound credits within the window. |

## Process

1. Collect inbound credits within the configured window, including this one.
2. If the count exceeds the limit, add severity scaled by the excess.
3. If the cumulative inbound amount exceeds the limit, add severity.
4. Emit an `inbound_velocity_burst` signal, or nothing.

## Outputs

Zero or one `RiskSignal` named `inbound_velocity_burst`.

## Reference Implementation

`src/inflow_monitor/skills/inflow_velocity.py`.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "Active accounts naturally see many credits." | Limits are configurable; tune them rather than ignoring the burst. |
| "Only the count matters." | Cumulative amount catches few-but-large bursts the count misses. |

## Red Flags

- The window or limits are hardcoded instead of read from configuration.
- The signal omits the count and cumulative amount from its evidence.

## Verification

- A burst above either limit yields a signal stating the count and the sum.
