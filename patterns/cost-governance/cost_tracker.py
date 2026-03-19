"""
Cost Governance Tracker
=======================

Track, control, and analyze LLM costs at the per-user and per-operation level.

Production lessons:
- Choosing the right model for each task is the single biggest cost lever
  (GPT-4.1 Nano at ~$0.00026/call vs GPT-4 at ~$0.03/call — 100x difference)
- Per-user cost tracking is essential for multi-tenant systems
- Budget alerts prevent surprises — catch cost spikes before they compound
- Some call sites are easy to miss — audit ALL LLM invocations regularly

Architecture:
- JSON-based cost records with per-user nesting
- Backward compatible with single-user systems
- Wired through all generation graphs and self-heal pipelines
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import json


class CostTier(Enum):
    """Model cost tiers for quick categorization."""
    NANO = "nano"           # < $0.001/call (small models, simple tasks)
    MICRO = "micro"         # $0.001 - $0.01/call (medium models)
    STANDARD = "standard"   # $0.01 - $0.05/call (large models)
    PREMIUM = "premium"     # > $0.05/call (largest models, complex tasks)


@dataclass
class ModelPricing:
    """Pricing configuration for a specific model."""
    model_id: str
    input_cost_per_1k: float    # Cost per 1,000 input tokens
    output_cost_per_1k: float   # Cost per 1,000 output tokens
    tier: CostTier
    display_name: str = ""

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a specific call."""
        input_cost = (input_tokens / 1000) * self.input_cost_per_1k
        output_cost = (output_tokens / 1000) * self.output_cost_per_1k
        return round(input_cost + output_cost, 6)


@dataclass
class CostRecord:
    """A single LLM cost event."""
    timestamp: str
    user_email: str
    operation: str              # e.g., "content_generation", "compliance_check"
    model_id: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    tier: CostTier
    metadata: dict = field(default_factory=dict)  # Additional context

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "user_email": self.user_email,
            "operation": self.operation,
            "model_id": self.model_id,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
            "tier": self.tier.value,
            "metadata": self.metadata,
        }


@dataclass
class BudgetAlert:
    """Budget threshold alert."""
    user_email: str
    alert_type: str             # "warning" (80%) or "exceeded" (100%)
    current_spend: float
    budget_limit: float
    period: str                 # "daily", "monthly"
    message: str


@dataclass
class CostSummary:
    """Cost summary for a user or system."""
    total_cost: float
    total_calls: int
    cost_by_operation: dict[str, float]
    cost_by_model: dict[str, float]
    cost_by_tier: dict[str, float]
    avg_cost_per_call: float
    period_start: str
    period_end: str

    def to_dict(self) -> dict:
        return {
            "total_cost_usd": round(self.total_cost, 4),
            "total_calls": self.total_calls,
            "avg_cost_per_call": round(self.avg_cost_per_call, 6),
            "cost_by_operation": {
                k: round(v, 4) for k, v in self.cost_by_operation.items()
            },
            "cost_by_model": {
                k: round(v, 4) for k, v in self.cost_by_model.items()
            },
            "cost_by_tier": {
                k: round(v, 4) for k, v in self.cost_by_tier.items()
            },
            "period": f"{self.period_start} to {self.period_end}",
        }


class CostTracker:
    """
    Per-user, per-operation LLM cost tracking with budget controls.

    Architecture decisions:
    - Per-user nesting: Each user's costs are tracked independently
    - Backward compatible: Works with or without user context
    - Budget alerts: Warning at 80%, block at 100% of configured limits
    - Operation categorization: Know WHERE money is being spent, not just how much
    """

    # Default model pricing (example rates)
    DEFAULT_PRICING = {
        "gpt-4.1-nano": ModelPricing(
            model_id="gpt-4.1-nano",
            input_cost_per_1k=0.0001,
            output_cost_per_1k=0.0004,
            tier=CostTier.NANO,
            display_name="GPT-4.1 Nano",
        ),
        "gpt-4.1-mini": ModelPricing(
            model_id="gpt-4.1-mini",
            input_cost_per_1k=0.0004,
            output_cost_per_1k=0.0016,
            tier=CostTier.MICRO,
            display_name="GPT-4.1 Mini",
        ),
        "gpt-4o": ModelPricing(
            model_id="gpt-4o",
            input_cost_per_1k=0.005,
            output_cost_per_1k=0.015,
            tier=CostTier.STANDARD,
            display_name="GPT-4o",
        ),
        "claude-sonnet-4": ModelPricing(
            model_id="claude-sonnet-4",
            input_cost_per_1k=0.003,
            output_cost_per_1k=0.015,
            tier=CostTier.STANDARD,
            display_name="Claude Sonnet 4",
        ),
    }

    def __init__(
        self,
        pricing: dict[str, ModelPricing] | None = None,
        daily_budget_usd: float = 10.0,
        monthly_budget_usd: float = 200.0,
    ):
        self.pricing = pricing or self.DEFAULT_PRICING
        self.daily_budget = daily_budget_usd
        self.monthly_budget = monthly_budget_usd
        self.records: list[CostRecord] = []
        self._user_daily_totals: dict[str, dict[str, float]] = {}

    def track(
        self,
        user_email: str,
        operation: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        metadata: dict | None = None,
    ) -> CostRecord:
        """
        Record a single LLM call's cost.

        This should be called after every LLM invocation — including
        self-heal repairs, compliance checks, and quality scoring calls.
        """
        pricing = self.pricing.get(model_id)
        if pricing:
            cost = pricing.calculate_cost(input_tokens, output_tokens)
            tier = pricing.tier
        else:
            # Unknown model — estimate conservatively
            cost = ((input_tokens + output_tokens) / 1000) * 0.01
            tier = CostTier.STANDARD

        record = CostRecord(
            timestamp=datetime.utcnow().isoformat(),
            user_email=user_email,
            operation=operation,
            model_id=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            tier=tier,
            metadata=metadata or {},
        )

        self.records.append(record)
        self._update_running_totals(record)

        return record

    def check_budget(self, user_email: str) -> Optional[BudgetAlert]:
        """
        Check if a user is approaching or exceeding budget limits.

        Returns an alert if action is needed, None if within budget.
        """
        today = datetime.utcnow().date().isoformat()
        daily_spend = self._get_daily_spend(user_email, today)

        # Check daily budget
        if daily_spend >= self.daily_budget:
            return BudgetAlert(
                user_email=user_email,
                alert_type="exceeded",
                current_spend=daily_spend,
                budget_limit=self.daily_budget,
                period="daily",
                message=(
                    f"Daily budget exceeded: ${daily_spend:.4f} / "
                    f"${self.daily_budget:.2f}"
                ),
            )
        elif daily_spend >= self.daily_budget * 0.8:
            return BudgetAlert(
                user_email=user_email,
                alert_type="warning",
                current_spend=daily_spend,
                budget_limit=self.daily_budget,
                period="daily",
                message=(
                    f"Approaching daily budget: ${daily_spend:.4f} / "
                    f"${self.daily_budget:.2f} (80% threshold)"
                ),
            )

        return None

    def get_user_summary(
        self,
        user_email: str,
        days: int = 30,
    ) -> CostSummary:
        """Get cost summary for a specific user over a time period."""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        user_records = [
            r
            for r in self.records
            if r.user_email == user_email and r.timestamp >= cutoff
        ]

        return self._build_summary(user_records, days)

    def get_system_summary(self, days: int = 30) -> CostSummary:
        """Get cost summary across all users."""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        recent = [r for r in self.records if r.timestamp >= cutoff]
        return self._build_summary(recent, days)

    def get_optimization_recommendations(self) -> list[str]:
        """
        Analyze cost patterns and suggest optimizations.

        Common recommendations:
        - Downgrade model for simple tasks
        - Cache repeated identical calls
        - Reduce token count through better prompting
        - Batch related calls
        """
        recommendations = []

        if not self.records:
            return ["No cost data available yet"]

        # Check for expensive models used on simple operations
        for record in self.records[-100:]:
            if (
                record.tier in (CostTier.STANDARD, CostTier.PREMIUM)
                and record.operation in ("compliance_check", "format_validation")
            ):
                recommendations.append(
                    f"Operation '{record.operation}' uses {record.model_id} "
                    f"(${record.cost_usd:.4f}/call). Consider a nano/micro "
                    "model for deterministic checks."
                )
                break

        # Check for high per-user spend
        user_totals: dict[str, float] = {}
        for record in self.records:
            user_totals[record.user_email] = (
                user_totals.get(record.user_email, 0) + record.cost_usd
            )

        for user, total in user_totals.items():
            if total > self.monthly_budget * 0.5:
                recommendations.append(
                    f"User {user} has spent ${total:.2f} — review their "
                    "usage patterns for optimization opportunities."
                )

        return recommendations or ["No optimization recommendations at this time"]

    def _update_running_totals(self, record: CostRecord):
        """Update running daily totals for budget checking."""
        today = datetime.utcnow().date().isoformat()
        user = record.user_email

        if user not in self._user_daily_totals:
            self._user_daily_totals[user] = {}

        current = self._user_daily_totals[user].get(today, 0.0)
        self._user_daily_totals[user][today] = current + record.cost_usd

    def _get_daily_spend(self, user_email: str, date: str) -> float:
        """Get total spend for a user on a specific date."""
        user_totals = self._user_daily_totals.get(user_email, {})
        return user_totals.get(date, 0.0)

    def _build_summary(
        self, records: list[CostRecord], days: int
    ) -> CostSummary:
        """Build a cost summary from a set of records."""
        total_cost = sum(r.cost_usd for r in records)
        total_calls = len(records)

        cost_by_operation: dict[str, float] = {}
        cost_by_model: dict[str, float] = {}
        cost_by_tier: dict[str, float] = {}

        for r in records:
            cost_by_operation[r.operation] = (
                cost_by_operation.get(r.operation, 0) + r.cost_usd
            )
            cost_by_model[r.model_id] = (
                cost_by_model.get(r.model_id, 0) + r.cost_usd
            )
            tier_name = r.tier.value
            cost_by_tier[tier_name] = (
                cost_by_tier.get(tier_name, 0) + r.cost_usd
            )

        end = datetime.utcnow()
        start = end - timedelta(days=days)

        return CostSummary(
            total_cost=total_cost,
            total_calls=total_calls,
            cost_by_operation=cost_by_operation,
            cost_by_model=cost_by_model,
            cost_by_tier=cost_by_tier,
            avg_cost_per_call=total_cost / total_calls if total_calls > 0 else 0,
            period_start=start.date().isoformat(),
            period_end=end.date().isoformat(),
        )
