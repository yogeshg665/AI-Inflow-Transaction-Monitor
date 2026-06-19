# Monitoring Policy

The decision agent maps the aggregate risk score to one of three outcomes using
configurable thresholds. The policy is deterministic and explainable.

## Outcomes

| Outcome | Condition | Meaning |
| --- | --- | --- |
| CLEAR | score < review threshold | Release the credit; continue passive monitoring. |
| REVIEW | review threshold <= score < flag threshold | Analyst due diligence; request source-of-funds. |
| FLAG | score >= flag threshold | Hold funds; open a suspicious-activity review. |

## Governance

- Flags and reviews must route to a human queue before any customer impact.
- A flag is a recommendation to investigate, not an automatic regulatory filing;
  the suspicious-activity determination is made by a human.
- Thresholds are defined in `config/config.yaml` and may be overridden by
  environment variables `RISK_FLAG_THRESHOLD` and `RISK_REVIEW_THRESHOLD`.
- Calibration from labeled feedback is advisory only and never mutates
  configuration automatically.

## Confidence

Confidence is derived from the score's margin to the nearest threshold: cases
far inside a band are reported with higher confidence than borderline cases.
