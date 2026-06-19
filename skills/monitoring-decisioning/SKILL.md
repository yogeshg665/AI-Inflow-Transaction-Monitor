---
name: monitoring-decisioning
description: Applies the monitoring policy to map a risk score and signals to a deterministic outcome of clear, review, or flag, with confidence and recommended actions. WHEN: "decide the outcome", "should this be flagged", "apply the monitoring policy", "clear review or flag", "what action for this inflow".
---

# Monitoring Decisioning

## Overview

Maps the aggregate score to one of three outcomes using the configured policy
thresholds, attaches the reasons (one per fired signal), and lists recommended
actions. Flags and reviews are routed for human handling.

## When to Use

- After scoring, to produce the case recommendation.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `case.risk_score` | yes | The aggregate score. |
| `decision_policy` | yes | The flag and review thresholds. |

## Process

1. If the score is at or above the flag threshold, recommend FLAG with hold and
   suspicious-activity-review actions.
2. Else if at or above the review threshold, recommend REVIEW with due-diligence
   actions.
3. Otherwise recommend CLEAR.
4. Set reasons from the triggered signals and compute a confidence from the
   score margin around the thresholds.

## Outputs

A `Decision` with outcome, confidence, reasons, and recommended actions.

## Reference Implementation

`src/inflow_monitor/agents/decision_agent.py`.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "Auto-block flagged funds without review." | Flags require human-review provisions before customer impact. |
| "Thresholds can be tuned in code." | Thresholds live in configuration and may be calibrated, not hardcoded. |

## Red Flags

- A flag or review outcome bypasses the human-review queue.
- The decision lists no reasons when signals were triggered.

## Verification

- The outcome matches the policy thresholds and cites the triggering signals.
