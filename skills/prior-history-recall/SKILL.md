---
name: prior-history-recall
description: Turns recalled collective memory into a corroborating, never-critical signal when an account or counterparty has adverse prior monitoring history. WHEN: "has this account been flagged before", "prior suspicious history", "recall past cases for this counterparty", "repeat offender check", "use memory in monitoring".
---

# Prior History Recall

## Overview

The read side of the optional collective-memory layer. When recall is enabled,
the orchestrator injects a prior-history summary into the case; this skill turns
adverse history into a corroborating signal that is never critical on its own.

## When to Use

- During detection, only when collective memory is enabled and recall found
  prior cases.
- Do NOT use it as a sole basis for a flag; it corroborates other signals.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `enrichment.memory_recall` | yes | Recall summary injected by the orchestrator. |

## Process

1. Read the recall summary from enrichment; stop if absent or empty.
2. Raise severity tiers for confirmed-suspicious prior cases, prior flags, and
   prior reviews, in that order of weight.
3. Emit an `adverse_prior_history` signal, always non-critical.

## Outputs

Zero or one `RiskSignal` named `adverse_prior_history` (never `critical`).

## Reference Implementation

`src/inflow_monitor/skills/prior_history.py`.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "Past flags should auto-flag the new case." | Memory corroborates; it is capped and never sets the score floor. |
| "Recall should run even when memory is off." | Memory is opt-in; with it disabled, this skill stays silent. |

## Red Flags

- The signal is marked critical.
- Recall performs I/O inside the skill instead of reading enrichment.

## Verification

- With prior adverse history present, a capped, non-critical signal is emitted.
