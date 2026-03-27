# Audit & Accountability Framework

**Structured methodology for auditing AI governance effectiveness**

---

## Why Audit Matters

Governance controls are only as good as their verification. Without structured auditing:
- Controls degrade silently over time
- New failure modes go undetected
- Compliance gaps emerge between rule updates
- Team confidence in the system erodes

This framework establishes a repeatable, adversarial audit methodology that treats AI governance like a security system — continuously tested, never assumed to work.

---

## Audit Hierarchy

A single auditor cannot catch everything. Different perspectives reveal different failures. This framework uses a **6-agent audit hierarchy** where each agent has a distinct mandate:

### Agent Roles

| Agent | Mandate | Perspective |
|---|---|---|
| **Regression Auditor** | Verify previously fixed issues stay fixed | Historical — "did we break old fixes?" |
| **Functional Auditor** | Verify features work as designed | Specification — "does it match requirements?" |
| **Stress Agent** | Push the system to failure under edge cases | Adversarial — "what breaks under pressure?" |
| **Devil's Advocate** | Actively attempt to circumvent governance controls | Red team — "can I make it produce bad output?" |
| **Validation Agent** | Verify audit findings are real, not false positives | Quality control — "is this finding legitimate?" |
| **Lead Auditor** | Synthesize findings, prioritize, and make go/no-go calls | Executive — "is this system ready for production?" |

### Audit Flow

```
Regression Auditor  ──┐
Functional Auditor  ──┤──→ Lead Auditor ──→ Go / No-Go Decision
Stress Agent        ──┤
Devil's Advocate    ──┘
         ↑
   Validation Agent (verifies any disputed findings)
```

---

## The Devil's Advocate Methodology

The most valuable audit perspective is adversarial. The Devil's Advocate agent doesn't verify that the system works — it tries to **prove the system fails**.

### Attack Categories

| Category | Description | Example |
|---|---|---|
| **Boundary Testing** | Push inputs to the edge of valid ranges | Maximum length inputs, unicode edge cases |
| **Compliance Evasion** | Try to make the system produce non-compliant output | Synonyms of banned phrases, context-dependent violations |
| **Quality Manipulation** | Try to produce low-quality output that passes validation | Gaming quality scores with keyword stuffing |
| **Hallucination Injection** | Try to make the system assert false claims | Contradictory source data, missing fields |
| **State Corruption** | Try to corrupt system state through malformed inputs | Invalid schemas, race conditions |
| **Logic Bypass** | Find paths that skip validation layers | Edge cases in conditional logic, error handling gaps |
| **Adversarial Prompting** | Attempt prompt injection through user-controllable fields | Instructions embedded in data fields |
| **Scale Attacks** | Issues that only appear at volume | Memory leaks, resource exhaustion, rate limit gaps |

### Scenario Packs

Pre-built adversarial test scenarios organized by domain:

```python
class ScenarioPack:
    """Reusable adversarial test scenarios for systematic coverage."""

    packs = {
        "compliance_evasion": [
            Scenario("synonym_substitution",
                     "Replace banned terms with synonyms and verify detection"),
            Scenario("context_dependent_violation",
                     "Use terms that are only violations in specific contexts"),
            Scenario("cross_language_evasion",
                     "Attempt violations using non-English terms or transliteration"),
            Scenario("fragmented_violation",
                     "Split banned phrases across sentences or paragraphs"),
        ],
        "hallucination_injection": [
            Scenario("missing_source_data",
                     "Generate with incomplete source data — verify no fabrication"),
            Scenario("contradictory_sources",
                     "Provide conflicting source data — verify handling"),
            Scenario("numeric_boundary",
                     "Test numeric claims near rounding boundaries"),
        ],
        "quality_gaming": [
            Scenario("keyword_stuffing",
                     "Test if quality scores can be gamed with keyword repetition"),
            Scenario("template_detection",
                     "Verify the system detects copy-paste template responses"),
            Scenario("minimum_viable_output",
                     "Find the lowest-quality output that still passes scoring"),
        ]
    }
```

---

## Regression Anchors

Every bug fix, governance improvement, or audit finding becomes a **regression anchor** — a permanent test that ensures the issue never recurs.

### Structure

```python
class RegressionAnchor:
    """Permanent test derived from a real governance failure."""

    def __init__(
        self,
        anchor_id: str,          # e.g., "R-42"
        description: str,         # What was the failure?
        root_cause: str,          # Why did it happen?
        fix_description: str,     # How was it fixed?
        test_input: dict,         # Input that triggered the failure
        expected_behavior: str,   # What should happen now
        layer: str,              # Which validation layer should catch this
        created_date: str,        # When was this anchor created
        session: str             # Which development session found it
    ):
        pass

    def verify(self, system: GovernedAISystem) -> AnchorResult:
        """Run the regression anchor and verify the fix holds."""
        output = system.generate(self.test_input)
        actual = self._extract_behavior(output)
        return AnchorResult(
            anchor_id=self.anchor_id,
            passed=actual == self.expected_behavior,
            expected=self.expected_behavior,
            actual=actual
        )
```

### Anchor Management

- **Never delete anchors** — they represent real failure modes
- **Anchors accumulate** — a mature system has 165+ anchors (proven in production)
- **Run all anchors** before every deployment
- **New anchors** are created from every audit finding and bug fix
- **Anchor density** indicates system maturity — more anchors = more battle-tested

---

## 4-Phase Audit Protocol

Every audit follows a mandatory 4-phase protocol:

### Phase 1: Regression Sweep
- Run all regression anchors
- Any failure is a **blocker** — no further progress until fixed
- Duration: Automated, typically < 5 minutes

### Phase 2: Functional Audit
- Verify all governance features against specifications
- Test each validation layer independently
- Verify remediation paths (self-heal, regeneration, escalation)
- Duration: 2-4 hours

### Phase 3: Adversarial Testing (Devil's Advocate)
- Run all applicable scenario packs
- Attempt novel attacks based on recent changes
- Document any governance bypasses found
- Duration: 4-8 hours

### Phase 4: Lead Auditor Review
- Synthesize findings from Phases 1-3
- Classify findings by severity and blast radius
- Make go/no-go decision with documented rationale
- Duration: 1-2 hours

### Go/No-Go Criteria

| Criterion | Go | No-Go |
|---|---|---|
| Regression anchors | 100% passing | Any failure |
| Critical findings | 0 open | Any open |
| High findings | All have mitigation plan | Unmitigated highs |
| Compliance validation | 0% leak rate | Any leaks |
| Quality scoring | Above threshold | Below threshold |

---

## Governance Documentation

Six foundational documents maintain governance integrity:

### 1. Decision Specification
Every significant governance decision is recorded:
```markdown
## Decision D-XX: [Title]
- **Date:** YYYY-MM-DD
- **Context:** What prompted this decision?
- **Decision:** What was decided?
- **Rationale:** Why this choice over alternatives?
- **Alternatives Considered:** What else was evaluated?
- **Constraints:** What limitations apply?
- **Review Trigger:** When should this decision be revisited?
```

### 2. Fix Closure Protocol
Every bug fix must demonstrate:
- Root cause identified (not just symptoms addressed)
- Fix implemented and tested
- Regression anchor created
- Related areas audited for same pattern
- Documentation updated

### 3. Audit Ownership & Tiers
- Tier 1 (Critical systems): Full 4-phase audit quarterly
- Tier 2 (High-risk systems): Functional + regression monthly
- Tier 3 (Moderate systems): Regression sweep weekly

### 4. Accepted Risk Register
Not every finding requires immediate fixing:
```markdown
## AR-XXX: [Risk Description]
- **Severity:** High/Medium/Low
- **Status:** ACCEPTED / MITIGATED / CLOSED
- **Rationale for Acceptance:** Why is this risk acceptable?
- **Mitigation:** What controls reduce the risk?
- **Review Date:** When will this be re-evaluated?
- **Owner:** Who is accountable?
```

### 5. Regression Anchor Registry
Central catalog of all regression anchors with:
- Anchor ID, description, and test definition
- Linked decision/fix that created it
- Last verification date and result

### 6. Evidence Minimums
Each audit tier has minimum evidence requirements:
- **Tier 1:** Full test suite, adversarial results, go/no-go sign-off
- **Tier 2:** Test suite results, spot-check findings
- **Tier 3:** Automated regression results

---

## Production Lock Methodology

Beyond periodic audits, systems that generate customer-facing output should go through a formal **production lock** process before being certified for production use.

### The Lock Protocol

```
1. Build & Stabilize    — System passes all unit and integration tests
2. Baseline Validation  — 100+ automated runs, measure clean rate
3. Full Validation      — 500+ automated runs, target ≥98% clean
4. Lock Specification   — Document architecture, known limitations, regression anchors
5. Lock Declaration     — System is certified; changes require re-validation
```

### Lock Specification Document

Every production-locked system has a formal spec:

```markdown
## Lock Spec: [System Name] v[Version]

### Architecture
- Pipeline stages and their order
- Mutation points (where content can change)
- Final integrity boundary (Last Mutation Boundary)

### Validation Results
- Total runs: 500
- Clean rate: 98.6% (493/500)
- Structural failures: 0
- Compliance failures: 0
- Transient errors: 7 (HTTP timeouts, race conditions)

### Known Limitations
- [Limitation 1] — Accepted risk with justification
- [Limitation 2] — Mitigated by [control]

### Regression Anchors
- R-001 through R-165 (linked to specific failure modes)

### Change Policy
- Any change to locked code requires re-running full validation
- Known limitations reviewed quarterly
- Lock spec updated with each re-validation
```

### Production Validation Methodology

Large-scale validation is not just "run it a lot." The methodology matters:

1. **Diverse inputs** — Cover sparse, medium, and rich source data
2. **Multiple profiles** — Test across all content types and configurations
3. **Failure classification** — Distinguish structural, compliance, quality, and transient failures
4. **Transient tolerance** — HTTP timeouts and race conditions are not system failures
5. **Zero-tolerance categories** — Compliance violations and structural failures must be 0

**Production result:** 493/500 clean (98.6%). 0 structural failures, 0 compliance failures, 0 hallucinations. 7 transient errors (4 HTTP timeouts, 2 compliance check exhaustion, 1 race condition).

---

## Continuous Audit Monitoring

Beyond periodic audits, continuous monitoring detects governance drift:

### Automated Monitors

| Monitor | Frequency | Alert Condition |
|---|---|---|
| Regression anchor suite | Every deployment | Any failure |
| Compliance violation rate | Daily | > 2x baseline |
| Quality score trend | Weekly | Declining 3+ weeks |
| Self-heal failure rate | Daily | > 15% |
| New pattern detection | Continuous | Unrecognized output patterns |

### Drift Detection

Governance drift occurs when:
- New AI model versions change output patterns
- New content types aren't covered by existing rules
- Rule updates create gaps in coverage
- Team changes lose institutional knowledge

**Counter-measure:** Every model update, content type addition, or rule change triggers a mini-audit (Phase 1 + targeted Phase 3).

---

## Maturity Model

Organizations can assess their AI audit maturity:

| Level | Description | Characteristics |
|---|---|---|
| **1 - Ad Hoc** | No structured auditing | Manual spot-checks, no regression tracking |
| **2 - Reactive** | Audit after incidents | Post-incident reviews, some regression tests |
| **3 - Structured** | Regular audit cadence | 4-phase protocol, regression anchors, documented decisions |
| **4 - Proactive** | Adversarial testing built-in | Devil's Advocate methodology, scenario packs, continuous monitoring |
| **5 - Predictive** | Anticipate failures before they occur | Drift detection, trend analysis, pre-emptive rule updates |

---

*The goal of auditing is not to find zero issues — it's to find issues before users do, and to have a system that gets stronger from every finding. A mature governance system treats audit findings as fuel for improvement, not failures to hide.*
