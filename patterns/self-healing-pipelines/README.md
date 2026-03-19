# Self-Healing Pipeline Patterns

Production patterns for AI systems that automatically detect and repair their own failures.

## Patterns in This Module

| Pattern | File | Description |
|---|---|---|
| Self-Healing Pipeline | `self_heal_pipeline.py` | Generate → Validate → Repair loop with bounded retries |

## Key Principles

1. **The user never sees a failure they can't act on** — either self-heal or "try again"
2. **Targeted repair over full regeneration** — fix only what's broken
3. **Bounded retries** — max 3 attempts, then escalate
4. **Every repair is logged** — audit trail for continuous improvement
5. **Self-heal success rate is a key health metric** — target ≥ 92%
