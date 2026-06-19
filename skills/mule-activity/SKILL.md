---
name: mule-activity
description: Detects mule-account behavior where an inbound credit is rapidly moved out again, measuring the outbound pass-through ratio within a short window after the credit. WHEN: "check for mule activity", "rapid in and out", "pass-through funds", "is this account draining the credit", "money mule detection".
---

# Mule Activity

## Overview

Flags credits that do not rest. It measures how much of a monitored inbound
credit is moved out within the pass-through window and raises a signal when the
drain ratio exceeds the configured threshold.

## When to Use

- During detection, for inbound credits at or above the minimum amount.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `event.amount` | yes | Inbound credit amount. |
| `account_history` | yes | Outbound movements after the credit within the window. |

## Process

1. Skip events below the configured minimum inbound amount.
2. Sum outbound movements that occur within the pass-through window after the
   credit.
3. Compute the pass-through ratio against the credit amount.
4. If the ratio meets the threshold, emit a `rapid_passthrough` signal.

## Outputs

Zero or one `RiskSignal` named `rapid_passthrough`.

## Reference Implementation

`src/inflow_monitor/skills/mule_activity.py`.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "People spend their money quickly." | Near-total, near-immediate drains are a distinct, well-known mule pattern. |
| "No outbound data means no risk." | Correct: absent outbound, the detector stays silent rather than guessing. |

## Red Flags

- A signal fires without any outbound movement in the window.
- The pass-through ratio is reported without the underlying amounts.

## Verification

- A high outbound drain after the credit yields a signal stating the ratio.
