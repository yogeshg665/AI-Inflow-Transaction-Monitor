# Monitoring Control Checklist

Run before closing any monitored case.

## Case integrity

- [ ] The inbound event passed schema validation.
- [ ] Account history is chronologically sorted.
- [ ] Only pseudonymous account and counterparty identifiers are present.
- [ ] No raw customer or banking-instrument data appears anywhere in the case.

## Detection

- [ ] Every detector ran; failures were isolated and logged, not silently
      swallowed into a missing score.
- [ ] Each fired signal has a non-empty rationale and supporting evidence.
- [ ] Any sanctioned-source hit is marked critical.

## Scoring and decision

- [ ] The score is reproducible for the same inputs.
- [ ] A critical signal set the score floor where applicable.
- [ ] The outcome matches the policy thresholds.

## Reporting and governance

- [ ] The report includes a reasoning trail with one entry per fired signal.
- [ ] Recommended actions are present and proportionate to the outcome.
- [ ] Flags and reviews route to a human queue before customer impact.
