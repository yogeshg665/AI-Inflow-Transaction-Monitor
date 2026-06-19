# Risk Scoring Rubric

The aggregate score is a confidence-weighted, configuration-weighted blend of
detector severities, with a corroboration boost and a critical floor, bounded to
0-100.

## Severity bands

| Severity | Meaning |
| --- | --- |
| 0 | Detector did not fire. |
| 1-39 | Weak indicator; contributes context. |
| 40-69 | Material indicator; meaningful on its own. |
| 70-100 | Strong indicator; often decisive in combination. |

## Confidence

Confidence (0-1) scales a signal's contribution. Detectors that infer behavior
from sparse data (for example, anomaly tests) carry lower confidence than
definitive checks (for example, a sanctions hit).

## Aggregation

1. Weighted blend: `severity x detector_weight x confidence`, averaged.
2. Corroboration boost: up to +25% as more independent detectors fire.
3. Critical floor: a critical signal raises the score to at least its severity.
4. Bound to 0-100.

## Score interpretation

| Score | Typical disposition |
| --- | --- |
| Below review threshold | CLEAR — release and monitor passively. |
| Review to flag threshold | REVIEW — analyst due diligence. |
| At or above flag threshold | FLAG — hold and suspicious-activity review. |

Thresholds live in `config/config.yaml` and may be tuned or calibrated; they are
never hardcoded.
