---
name: cross-border-risk
description: Flags cross-border inflows and currency mismatches against the account's home setup, adding severity for high-risk origin corridors. WHEN: "is this a cross-border inflow", "foreign source funds", "currency mismatch on a credit", "high-risk corridor", "international inbound transfer risk".
---

# Cross-Border Risk

## Overview

Raises risk when inbound funds cross a border or arrive in a currency that does
not match the account's home currency, with extra severity for high-risk origin
corridors. These factors do not imply wrongdoing alone but materially raise
laundering risk.

## When to Use

- During detection, for every inbound credit.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `event.source_country` | yes | Origin country of the funds. |
| `event.account_country` | yes | Booking country of the account. |
| `event.currency` | yes | Currency of the credit. |

## Process

1. If the source country differs from the account country, add cross-border
   severity.
2. If the origin is a configured high-risk corridor, add further severity.
3. If the currency differs from the configured home currency, add severity.
4. Emit a `cross_border_inflow` signal, or nothing.

## Outputs

Zero or one `RiskSignal` named `cross_border_inflow`.

## Reference Implementation

`src/inflow_monitor/skills/cross_border.py`.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "Cross-border is normal for many accounts." | It is weighted modestly; the score combines it with other signals. |
| "Currency mismatch is harmless." | It is a recognized layering indicator and is included by design. |

## Red Flags

- The home currency is hardcoded instead of read from configuration.
- The rationale does not name the countries or currencies involved.

## Verification

- A foreign-origin or currency-mismatched credit yields a clear cross-border
  signal.
