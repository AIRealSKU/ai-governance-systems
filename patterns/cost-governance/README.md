# Cost Governance Patterns

Production patterns for tracking, controlling, and optimizing AI/LLM operational costs.

## Patterns in This Module

| Pattern | File | Description |
|---|---|---|
| Cost Tracker | `cost_tracker.py` | Per-user, per-operation LLM cost tracking with budget controls |

## Key Principles

1. **Every LLM call has a cost** — track it or lose control at scale
2. **Per-user tracking** enables fair billing and abuse detection
3. **Budget controls prevent runaway costs** — alert before it's a problem
4. **Model selection affects cost 100x** — choose the right model for each task
5. **Cost per operation, not cost per token** — users care about outcomes, not internals
