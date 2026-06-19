---
name: credit-anomaly
description: Detects inbound credits that are statistical outliers versus the account's historical inbound baseline, using both a z-score and a multiple-of-mean test. WHEN: "is this credit unusual for the account", "anomalous inbound amount", "outlier deposit", "credit far above baseline", "statistical anomaly on a credit".
---

# Credit Anomaly

## Overview

Builds a baseline from the account's prior inbound amounts and flags a monitored
credit that is a statistical outlier, either by z-score or by a simple multiple
of the historical mean.

## When to Use

- During detection, when the account has at least the minimum inbound history.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `event.amount` | yes | Inbound credit amount. |
| `account_history` | yes | Prior inbound credits forming the baseline. |

## Process

1. Collect prior inbound amounts for the account; require the minimum history.
2. Compute the mean and standard deviation.
3. If the z-score meets the threshold, add severity scaled by the excess.
4. If the amount is at least the configured multiple of the mean, add severity.
5. Emit an `anomalous_credit` signal, or nothing.

## Outputs

Zero or one `RiskSignal` named `anomalous_credit`.

## Reference Implementation

`src/inflow_monitor/skills/credit_anomaly.py`.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "Thin history should still trigger." | Below the minimum, the baseline is unreliable; the detector stays silent. |
| "A z-score alone is enough." | The multiple-of-mean test catches wide distributions the z-score misses. |

## Red Flags

- A signal fires with fewer than the minimum prior inbound records.
- The baseline mean is not reported in the evidence.

## Verification

- An outlier credit yields a signal citing the z-score or the multiple of mean.
