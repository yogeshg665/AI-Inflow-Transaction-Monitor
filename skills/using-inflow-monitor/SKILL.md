---
name: using-inflow-monitor
description: Meta-skill that routes an inbound-transaction monitoring request to the correct workflow and defines the shared operating rules. WHEN: "monitor this deposit", "is this inflow suspicious", "review an incoming transfer", "flag suspicious inbound funds", "AML check on a credit", "start transaction monitoring", "which monitoring skill applies".
---

# Using the Inflow Transaction Monitor

## Overview

This is the entry point for the pack. It explains the monitoring lifecycle,
routes a request to the right skill, and states the rules every skill must
follow. Read this first.

## When to Use

- At the start of any inbound-transaction monitoring request.
- When unsure which detector or stage applies.

## Lifecycle

Run the stages in order. Each stage has a dedicated skill.

1. **Intake** — `inflow-intake`: validate and normalize the inbound event.
2. **Enrichment** — `counterparty-enrichment`: add baseline and reference context.
3. **Detection** — run the detector swarm:
   - `structuring-detection`
   - `mule-activity`
   - `credit-anomaly`
   - `source-screening`
   - `inflow-velocity`
   - `cross-border-risk`
   - `prior-history-recall`
4. **Scoring** — `risk-scoring`: blend signals into one score.
5. **Decisioning** — `monitoring-decisioning`: clear, review, or flag.
6. **Reporting** — `case-reporting`: produce the audit-ready report.

## Process

1. Identify the request type and locate the inbound event payload.
2. Run intake and enrichment to build the case.
3. Run every detector; each emits at most one explainable signal.
4. Aggregate to a score, apply the policy, and produce the report.

## Operating Rules

1. Every flag must be explainable and cite its signals.
2. Scoring and decisions are deterministic. A language model may enrich the
   narrative only; it must never change the score or the decision.
3. Use pseudonymous account and counterparty identifiers. Never request or store
   raw customer or banking-instrument data.
4. Flags and reviews require human-review provisions before any customer impact.
5. Collective memory is optional and off by default. When enabled, recall and
   feedback remain deterministic, the memory signal is never critical, and
   threshold calibration is advisory only.

## Outputs

A routed workflow and a shared rule set that every downstream skill honors.

## Verification

- The correct lifecycle stage and skill are selected for the request.
- The operating rules above are applied throughout the case.
