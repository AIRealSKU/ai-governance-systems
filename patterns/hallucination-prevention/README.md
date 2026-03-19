# Hallucination Prevention Patterns

Production-tested patterns for preventing AI hallucinations in governed systems.

## Patterns in This Module

| Pattern | File | Description |
|---|---|---|
| Validation Gate | `validation_gate.py` | Multi-pass validation with factual grounding checks |
| Banned Content Detector | `banned_content_detector.py` | High-performance phrase detection with 500+ patterns |
| Factual Router | `factual_router.py` | Route claims through type-specific verification |

## Key Principles

1. **Assume all AI claims are unverified** until matched against source data
2. **Post-processing over prompting** — deterministic checks catch what prompts miss
3. **Extraction is critical infrastructure** — bad source extraction poisons all downstream validation
4. **Per-claim verification** — validate individual claims, not entire outputs
