# Output Quality Scoring Patterns

Production patterns for multi-dimensional AI output quality assessment.

## Patterns in This Module

| Pattern | File | Description |
|---|---|---|
| Quality Scorer | `quality_scorer.py` | Composite scoring with per-dimension breakdown and thresholds |

## Key Principles

1. **Quality is multi-dimensional** — a single score hides important signals
2. **Thresholds are business decisions** — engineering provides the measurement, stakeholders set the bar
3. **First-pass clean rate is a health indicator** — ≥25% healthy, <15% danger zone
4. **Targeted improvement over "try again"** — tell the generator WHAT to improve
5. **Quality gates enforce minimum standards** — no output ships below threshold
