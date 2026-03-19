# Case Study: Governing Multi-Agent AI Systems

---

## Context

A production system uses 5+ specialized AI agents orchestrated through a graph-based pipeline (LangGraph). Each agent has a distinct role — content generation, compliance checking, quality assessment, repair, and orchestration. The system must produce outputs that are compliant, high-quality, and cost-effective.

**Challenge:** When multiple AI agents collaborate, governance becomes exponentially more complex. Each agent can introduce failures, and failures can compound across the pipeline. Traditional single-model governance approaches don't scale to multi-agent systems.

---

## The Problem

### Agent Coordination Failures
- Agent A generates content that Agent B's compliance check rejects, triggering Agent C's repair, which Agent B rejects again → infinite loop
- No bounded retry limits → system hung on difficult inputs
- No visibility into which agent caused the failure

### Cost Amplification
- Each agent makes LLM calls independently
- Self-heal loops multiply costs (3 repair attempts × 5 agents = 15+ LLM calls)
- No cost tracking per agent → no optimization visibility
- One pathological input could trigger $5+ in LLM costs

### Accountability Gaps
- When output quality is poor, which agent is responsible?
- When compliance violations leak through, which checkpoint failed?
- When costs spike, which agent is the cause?

---

## Solution: Agent Governance Framework

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                     │
│         (State management, routing, cost control)        │
├─────────┬────────────┬────────────┬────────────┬────────┤
│ Content │ Compliance │  Quality   │   Repair   │ Export │
│  Agent  │   Agent    │   Agent    │   Agent    │ Agent  │
├─────────┴────────────┴────────────┴────────────┴────────┤
│              Shared Governance Layer                      │
│    (Cost tracking, audit logging, circuit breakers)       │
└─────────────────────────────────────────────────────────┘
```

### Key Governance Mechanisms

**1. Agent Contracts**

Each agent operates under a defined contract:

```python
@dataclass
class AgentContract:
    """Defines the governance boundaries for an AI agent."""
    agent_name: str
    max_llm_calls: int           # Maximum LLM calls per invocation
    max_cost_per_call: float     # Cost ceiling per invocation
    timeout_seconds: int         # Maximum execution time
    required_inputs: list[str]   # Must receive these fields
    guaranteed_outputs: list[str] # Must produce these fields
    error_budget: float          # Acceptable failure rate (e.g., 0.05 = 5%)
    fallback_behavior: str       # What to do on failure: "retry", "degrade", "skip"
```

**2. Circuit Breakers**

Prevent cascade failures and infinite loops:

```python
class AgentCircuitBreaker:
    """
    Breaks the circuit when an agent is failing too frequently.

    States:
    - CLOSED: Normal operation
    - OPEN: Agent is failing, bypass with fallback
    - HALF_OPEN: Testing if agent has recovered
    """

    def __init__(self, failure_threshold: int = 3, reset_timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.state = "CLOSED"
        self.last_failure_time = None

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.last_failure_time = datetime.now()

    def should_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            # Check if reset timeout has elapsed
            if self._timeout_elapsed():
                self.state = "HALF_OPEN"
                return True
            return False
        # HALF_OPEN: allow one attempt
        return True
```

**3. Per-Agent Cost Tracking**

Every LLM call is attributed to its originating agent:

```python
class AgentCostTracker:
    """Track costs at agent granularity for optimization."""

    def track_call(self, agent_name: str, model: str,
                   input_tokens: int, output_tokens: int):
        cost = self.pricing.calculate(model, input_tokens, output_tokens)

        self.records.append({
            "agent": agent_name,
            "model": model,
            "cost": cost,
            "timestamp": datetime.now().isoformat()
        })

        # Check agent budget
        agent_total = self._get_agent_total(agent_name)
        if agent_total > self.agent_budgets.get(agent_name, float('inf')):
            raise AgentBudgetExceeded(agent_name, agent_total)
```

**4. Graph-Level State Management**

The orchestrator manages state transitions with governance checkpoints:

```python
class GovernedGraph:
    """
    LangGraph-based pipeline with governance checkpoints at each transition.

    Key principle: State transitions are the governance checkpoints.
    Before an agent can pass output to the next agent, it must satisfy
    its contract's guaranteed_outputs requirement.
    """

    def __init__(self):
        self.agents = {}
        self.contracts = {}
        self.circuit_breakers = {}
        self.cost_tracker = AgentCostTracker()

    def add_agent(self, agent, contract: AgentContract):
        self.agents[contract.agent_name] = agent
        self.contracts[contract.agent_name] = contract
        self.circuit_breakers[contract.agent_name] = AgentCircuitBreaker()

    def execute_agent(self, agent_name: str, state: dict) -> dict:
        contract = self.contracts[agent_name]
        breaker = self.circuit_breakers[agent_name]

        # Pre-check: circuit breaker
        if not breaker.should_execute():
            return self._apply_fallback(agent_name, state)

        # Pre-check: required inputs
        missing = [f for f in contract.required_inputs if f not in state]
        if missing:
            raise AgentInputViolation(agent_name, missing)

        # Execute with timeout and cost tracking
        try:
            result = self._execute_with_timeout(
                agent_name, state, contract.timeout_seconds
            )

            # Post-check: guaranteed outputs
            missing_outputs = [
                f for f in contract.guaranteed_outputs if f not in result
            ]
            if missing_outputs:
                raise AgentOutputViolation(agent_name, missing_outputs)

            breaker.record_success()
            return result

        except Exception as e:
            breaker.record_failure()
            self._log_agent_failure(agent_name, e)

            if contract.fallback_behavior == "degrade":
                return self._apply_fallback(agent_name, state)
            elif contract.fallback_behavior == "skip":
                return state  # Pass through unchanged
            else:
                raise
```

---

## Results

| Metric | Before | After | Improvement |
|---|---|---|---|
| Infinite loop incidents | 2-3/week | 0 | Eliminated |
| Average pipeline cost | $0.12/run | $0.03/run | 75% reduction |
| Agent failure visibility | None | Per-agent dashboards | Full observability |
| Mean pipeline time | 18.2 seconds | 3.4 seconds | 81% faster |
| Overall success rate | 71% | 92% | +21 percentage points |

### Cost Reduction Breakdown

The 75% cost reduction came from three sources:
1. **Model right-sizing:** Compliance checks switched from GPT-4 to GPT-4.1 Nano (100x cheaper per call, same accuracy for deterministic tasks)
2. **Circuit breakers:** Stopped wasting money on agents that were clearly failing
3. **Bounded retries:** Maximum 3 repair attempts instead of unlimited loops

---

## Lessons Learned

### 1. Agent Contracts Prevent Scope Creep
Without contracts, agents gradually expand their behavior — the compliance agent starts "improving" content, the repair agent introduces new features. Contracts keep each agent focused on its mandate.

### 2. Cost Tracking Must Be Per-Agent
System-level cost tracking hides the real story. When we added per-agent tracking, we discovered:
- The repair agent accounted for 60% of costs (3+ LLM calls per repair)
- The compliance agent could run on a nano model (no reasoning needed, just pattern matching)
- The content agent's cost was appropriate but could be cached for similar inputs

### 3. Circuit Breakers Are Essential
Before circuit breakers, a single pathological input could cascade through the entire pipeline, consuming resources and blocking other requests. Circuit breakers isolate failures and maintain throughput for healthy inputs.

### 4. Graph State Is the Audit Trail
By logging state transitions between agents, we got a complete audit trail for free. Every output can be traced back through each agent's contribution, making debugging and compliance auditing straightforward.

### 5. Parallel Where Possible, Sequential Where Required
Not all agents need to run in sequence. Content generation for different asset types can run in parallel. But compliance validation MUST run after generation. The graph explicitly encodes these dependencies.

---

## Governance Dashboard

The agent governance dashboard surfaces:

| Panel | Metrics |
|---|---|
| **Agent Health** | Success rate, latency, error rate per agent |
| **Cost Attribution** | Cost per agent, per model, trending |
| **Circuit Breaker Status** | Open/closed/half-open per agent |
| **Contract Compliance** | Input/output violations, timeout breaches |
| **Pipeline Flow** | Live view of requests moving through the graph |

---

## Applicability

This pattern applies to any multi-agent AI system where:
- Multiple AI models or agents collaborate on a task
- Individual agent failures should not cascade to the entire system
- Cost control and attribution matter at scale
- Audit trail and accountability are required per agent
- System reliability must exceed any individual agent's reliability

**Use cases:** Content generation pipelines, customer service automation, document processing workflows, decision support systems, any LangChain/LangGraph-based multi-agent system.

---

*The key insight: governing a multi-agent system is not about governing each agent in isolation — it's about governing the interactions between agents. Contracts, circuit breakers, and graph-level state management turn a fragile chain of AI calls into a resilient, observable, and cost-controlled pipeline.*
