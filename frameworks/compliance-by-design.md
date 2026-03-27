# Compliance-by-Design: Embedding Regulatory Controls into AI Pipelines

---

## The Problem

Most organizations treat compliance as a review step — AI generates output, then someone checks if it's compliant. This approach fails at scale because:

1. **Manual review is a bottleneck** — Compliance teams can't review every AI-generated output
2. **Post-hoc fixes are expensive** — Catching violations after generation wastes compute and time
3. **Inconsistency is inevitable** — Human reviewers apply standards differently
4. **Coverage gaps emerge** — Not every output gets reviewed, creating risk

**The alternative:** Build compliance into the generation pipeline itself, so non-compliant outputs are impossible — not just unlikely.

---

## Core Principle: Deterministic Rules + AI Reasoning

Compliance requirements are binary — an output is either compliant or it isn't. AI is probabilistic. This creates a fundamental tension.

**Resolution:** Use a hybrid architecture:

| Layer | Technology | Purpose |
|---|---|---|
| **Generation** | LLM (AI) | Creative language, reasoning, pattern recognition |
| **Compliance Enforcement** | Deterministic rules | Policy enforcement, banned content, required disclosures |
| **Quality Assessment** | AI + Rules | Scoring, ranking, threshold enforcement |
| **Repair** | AI guided by rules | Fix violations while preserving intent |

The key insight: **post-processing beats prompt engineering for compliance**. You cannot reliably instruct an LLM to never use certain phrases. But you can deterministically scan outputs and remove violations with 100% accuracy.

---

## Architecture

### Layer 1: Input Sanitization

Before any AI generation occurs:

```python
class InputSanitizer:
    """Sanitize inputs to prevent compliance violations from entering the pipeline."""

    def __init__(self, rules_registry: ComplianceRulesRegistry):
        self.rules = rules_registry

    def sanitize(self, input_data: dict) -> SanitizedInput:
        """
        Remove or flag content that could lead to compliance violations.

        Examples:
        - Strip agent contact info from source data (prevents unauthorized disclosure)
        - Flag discriminatory language in user-provided descriptions
        - Validate required fields are present before generation
        """
        violations = []
        cleaned = input_data.copy()

        for rule in self.rules.get_input_rules():
            result = rule.check(cleaned)
            if result.violated:
                cleaned = rule.remediate(cleaned)
                violations.append(result)

        return SanitizedInput(
            data=cleaned,
            violations_found=len(violations),
            violations_remediated=violations,
            audit_trail=self._build_audit_trail(violations)
        )
```

### Layer 2: Bounded Generation

Constrain AI outputs through structure, not just instructions:

```python
class BoundedGenerator:
    """Generate AI content within compliance boundaries."""

    def generate(self, context: GenerationContext) -> BoundedOutput:
        # Structure-first: Define the skeleton before AI fills it
        template = self.get_compliance_template(context.content_type)

        # Required disclosures are system-inserted, not AI-generated
        disclosures = self.rules.get_required_disclosures(context)

        # AI generates within bounded sections
        ai_sections = {}
        for section in template.ai_sections:
            ai_sections[section.name] = self.llm.generate(
                prompt=section.prompt,
                constraints=section.compliance_constraints,
                max_tokens=section.max_length  # Prevent runaway generation
            )

        return BoundedOutput(
            template=template,
            ai_content=ai_sections,
            system_disclosures=disclosures,
            generation_metadata=self._capture_metadata()
        )
```

### Layer 3: Deterministic Compliance Scan

Every output passes through rule-based scanning:

```python
class ComplianceScanner:
    """Deterministic compliance validation — no AI, no ambiguity."""

    def __init__(self):
        self.banned_phrases = BannedPhraseRegistry()  # 500+ phrases
        self.required_elements = RequiredElementRegistry()
        self.format_rules = FormatRuleRegistry()

    def scan(self, output: BoundedOutput) -> ComplianceResult:
        violations = []

        # Check 1: Banned content (exact match + pattern match)
        for phrase in self.banned_phrases.get_all():
            if phrase.matches(output.text):
                violations.append(ComplianceViolation(
                    type="BANNED_CONTENT",
                    phrase=phrase,
                    location=phrase.find_location(output.text),
                    severity=phrase.severity,
                    auto_fixable=phrase.has_safe_alternative
                ))

        # Check 2: Required elements present
        for element in self.required_elements.get_for_type(output.content_type):
            if not element.present_in(output):
                violations.append(ComplianceViolation(
                    type="MISSING_REQUIRED",
                    element=element,
                    severity="HIGH",
                    auto_fixable=element.has_default
                ))

        # Check 3: Format compliance
        for rule in self.format_rules.get_for_type(output.content_type):
            if not rule.satisfied_by(output):
                violations.append(ComplianceViolation(
                    type="FORMAT_VIOLATION",
                    rule=rule,
                    severity=rule.severity,
                    auto_fixable=True
                ))

        return ComplianceResult(
            compliant=len(violations) == 0,
            violations=violations,
            auto_fixable_count=sum(1 for v in violations if v.auto_fixable),
            requires_regeneration=any(v.severity == "CRITICAL" for v in violations)
        )
```

### Layer 4: Self-Healing Remediation

Violations are fixed automatically when possible:

```python
class ComplianceRemediator:
    """Fix compliance violations without regenerating from scratch."""

    def remediate(self, output: BoundedOutput, violations: list) -> RemediatedOutput:
        remediated = output.text
        changes = []

        for violation in sorted(violations, key=lambda v: v.severity, reverse=True):
            if violation.type == "BANNED_CONTENT" and violation.auto_fixable:
                # Replace banned phrase with safe alternative
                safe_alt = self.banned_phrases.get_alternative(violation.phrase)
                remediated = remediated.replace(
                    violation.phrase.text,
                    safe_alt
                )
                changes.append(RemediationChange(
                    type="REPLACEMENT",
                    original=violation.phrase.text,
                    replacement=safe_alt,
                    reason=violation.phrase.regulation
                ))

            elif violation.type == "MISSING_REQUIRED":
                # Insert required element at appropriate position
                remediated = self._insert_required(
                    remediated,
                    violation.element
                )
                changes.append(RemediationChange(
                    type="INSERTION",
                    element=violation.element.name,
                    reason="Regulatory requirement"
                ))

        # Re-scan after remediation to verify
        rescan = self.scanner.scan(remediated)

        return RemediatedOutput(
            text=remediated,
            changes=changes,
            fully_remediated=rescan.compliant,
            audit_trail=self._build_audit_trail(changes)
        )
```

---

## Advanced Compliance Patterns

### Trust-Tiered Claim Model

Not all data in an AI system has the same credibility. A trust-tiered model assigns every factual claim a trust level, then enforces rendering rules based on that level:

```python
class TrustTier(Enum):
    """5-tier trust classification for factual claims."""
    VERIFIED = "verified"           # Confirmed by authoritative source (e.g., official database)
    AGENT_DECLARED = "agent_declared"  # Stated by a human operator, unverified
    DERIVED = "derived"             # Inferred from verified data through rules
    GENERATED = "generated"         # Produced by AI — lowest trust before blocked
    BLOCKED = "blocked"             # Fails compliance — must not appear in output

@dataclass
class Claim:
    """A single factual assertion with trust metadata."""
    text: str
    trust_tier: TrustTier
    source: str                     # Where this claim originated
    confidence: float               # 0.0-1.0 confidence in the claim
    verified_at: Optional[datetime] # When verification occurred


class ClaimInventory:
    """Central registry of all claims for a given context."""

    def get_claims_for_mode(self, rendering_mode: str) -> list[Claim]:
        """
        Mode-scoped rendering: different output contexts allow different trust levels.

        - "strict" mode: Only VERIFIED claims (e.g., official documents)
        - "standard" mode: VERIFIED + AGENT_DECLARED (e.g., marketing content)
        - "internal" mode: All non-blocked claims (e.g., draft review)
        """
        allowed_tiers = self.MODE_TIERS[rendering_mode]
        return [c for c in self.claims if c.trust_tier in allowed_tiers]
```

**Why this matters:** Without trust tiers, AI systems treat all data equally — an unverified AI-generated claim gets the same prominence as a database-confirmed fact. Trust tiers prevent this by making trust explicit and rendering rules enforceable.

### 3-Layer Writing Policy Architecture

When AI generates text that must comply with regulations, a single prompt instruction is insufficient. A 3-layer architecture provides defense in depth:

```
Layer 1: Source Control     — Control what the AI is asked to write
Layer 2: Kill Switches      — Deterministic removal of prohibited content
Layer 3: Controlled Vocabulary — Restrict the output to approved language
```

**Layer 1: Source Control** — Prompt hardening, positive/negative examples, temperature reduction. Reduces the probability of violations at generation time.

**Layer 2: Kill Switches** — Deterministic post-processing that removes specific categories of prohibited content. Each kill switch targets a category (e.g., calls-to-action, exclamation marks, person-targeting language, promotional verbs, filler phrases). Kill switches are binary — content either passes or is stripped.

**Layer 3: Controlled Vocabulary** — An approved vocabulary of adjectives, phrases, and sentence patterns. Content containing unapproved embellishments, superlatives, or domain-specific prohibited terms is stripped and replaced with neutral alternatives.

```python
class WritingPolicyEnforcer:
    """3-layer writing policy enforcement."""

    def enforce(self, text: str, policy_profile: str) -> str:
        # Layer 1 already applied at generation time (prompt + temperature)

        # Layer 2: Kill switches (deterministic removal)
        for switch in self.kill_switches.get_for_profile(policy_profile):
            text = switch.apply(text)

        # Layer 3: Controlled vocabulary
        text = self.vocabulary_filter.enforce(text, policy_profile)

        return text
```

**Production result:** This 3-layer approach reduced compliance violations from ~15% (prompt-only) to 0% (post-processing), while maintaining content quality scores above 8.0/10.

### Shared Integrity Layer

When a system produces multiple output types (emails, social posts, documents, structured data), each type needs compliance enforcement — but duplicating enforcement logic creates inconsistency and maintenance burden.

A **shared integrity layer** provides a single, reusable enforcement pipeline that adapts to each content type through profiles:

```python
class IntegrityProfile:
    """Content-type-specific enforcement configuration."""
    content_type: str            # e.g., "email", "social", "document"
    block_aware: bool            # Whether to process by blocks (paragraphs, bullets)
    skipped_checks: list[str]    # Checks to skip for this content type
    scoring_weights: dict        # Custom weights for quality dimensions


class SharedIntegrityLayer:
    """
    Reusable enforcement layer across all content types.

    Same core logic, different profiles. One place to fix, one place to audit.
    """

    def enforce(self, content: str, profile: IntegrityProfile) -> str:
        # Block-aware processing: paragraphs and bullets treated differently
        if profile.block_aware:
            blocks = self._segment_blocks(content)
            enforced_blocks = [
                self._enforce_block(block, profile) for block in blocks
            ]
            return self._reassemble(enforced_blocks)
        else:
            return self._enforce_block(content, profile)

    def _enforce_block(self, block: str, profile: IntegrityProfile) -> str:
        """Apply all enforcement steps to a single block."""
        for step in self.enforcement_steps:
            if step.name not in profile.skipped_checks:
                block = step.apply(block)
        return block
```

**Key benefit:** When a compliance rule is updated, it takes effect across all content types simultaneously. No drift, no missed types, no inconsistency.

### Compliance Rules Engine

For organizations operating across multiple jurisdictions, compliance rules must be externalized from code and managed as data:

```python
class ComplianceRulesEngine:
    """
    Externalized compliance rules with admin workflow.

    Lifecycle: Upload source → AI extraction → Admin review → Promote → Enforce
    """

    def ingest_rules(self, source_document: bytes, jurisdiction: str):
        """
        Extract compliance rules from regulatory documents.

        1. AI extracts candidate rules from source (PDF, HTML, etc.)
        2. Deterministic classifier categorizes each rule
        3. Admin reviews and approves/rejects each rule
        4. Approved rules are promoted into the enforcement pipeline
        5. Deduplication prevents the same rule from being added twice
        """
        candidates = self.extractor.extract(source_document)
        classified = self.classifier.classify(candidates)
        return PendingRuleSet(
            rules=classified,
            jurisdiction=jurisdiction,
            status="PENDING_REVIEW",
            audit_trail=self._build_trail(source_document)
        )

    def promote_rule(self, rule_id: str, admin_email: str):
        """Promote a reviewed rule into active enforcement."""
        rule = self.get_rule(rule_id)
        rule.status = "ACTIVE"
        rule.promoted_by = admin_email
        rule.promoted_at = datetime.now()
        self.audit_log.record("RULE_PROMOTED", rule_id, admin_email)
```

**Rule types:**
- **Structural rules:** Full prompt-level instructions (e.g., "descriptions must not exceed 1000 characters")
- **Hard blocks:** Deterministic phrase/pattern blocks compressed into the enforcement pipeline
- **Soft guidance:** Advisory rules that flag but don't block (e.g., "prefer active voice")

---

## Design Principles

### 1. The User Never Fixes Compliance

If a compliance violation is detected, the system fixes it automatically. The user sees either:
- **Success** — compliant output delivered
- **Try again** — system could not auto-fix, requests regeneration

The user is never presented with a compliance violation to manually resolve. This prevents:
- User fatigue leading to ignored warnings
- Inconsistent manual fixes
- Compliance knowledge requirements pushed to end users

### 2. Post-Processing Over Prompt Engineering

| Approach | Reliability | Why |
|---|---|---|
| "Don't use discriminatory language" in prompt | ~85% | LLMs are probabilistic — instructions are not guarantees |
| Deterministic scan + replace after generation | 100% | Rule-based scanning has no false negatives for known patterns |

**Rule:** Any compliance requirement that can be expressed as a deterministic rule MUST be enforced through post-processing, not prompting.

### 3. Separation of Compliance Domains

Different regulations have different enforcement patterns:

```python
class ComplianceRulesRegistry:
    """Each compliance domain is independently managed and versioned."""

    domains = {
        "fair_housing": FairHousingRules(),      # FHA protected classes
        "fair_lending": FairLendingRules(),       # ECOA/HMDA requirements
        "data_privacy": DataPrivacyRules(),       # PII handling
        "advertising": AdvertisingRules(),        # Truth in advertising
        "accessibility": AccessibilityRules(),    # ADA compliance
    }

    def get_rules_for_context(self, context: GenerationContext) -> list:
        """Return applicable rules based on content type and jurisdiction."""
        applicable = []
        for domain_name, domain_rules in self.domains.items():
            if domain_rules.applies_to(context):
                applicable.extend(domain_rules.get_active_rules())
        return applicable
```

### 4. Compliance Rules Are Living Documents

Regulatory requirements change. The system must accommodate:

```python
class RuleVersioning:
    """Track rule changes with effective dates and audit trail."""

    def update_rule(self, rule_id: str, new_version: RuleVersion):
        # Never delete old rules — mark as superseded
        old_rule = self.get_rule(rule_id)
        old_rule.status = "SUPERSEDED"
        old_rule.superseded_by = new_version.id
        old_rule.superseded_date = datetime.now()

        # New rule includes effective date
        new_version.effective_date = new_version.effective_date
        new_version.previous_version = old_rule.id

        self.save(new_version)
        self.audit_log.record(
            action="RULE_UPDATE",
            old_version=old_rule.id,
            new_version=new_version.id,
            reason=new_version.change_reason
        )
```

---

## Measuring Compliance-by-Design Effectiveness

| Metric | Target | Measurement |
|---|---|---|
| Pre-remediation violation rate | Trending down | How often does raw AI output violate? |
| Auto-remediation success rate | ≥ 92% | How often can violations be fixed without regeneration? |
| Post-remediation leak rate | 0% | How often do violations reach production? |
| False positive rate | < 5% | How often does the scanner flag compliant content? |
| Remediation latency | < 500ms | How long does compliance processing add? |

---

## Enterprise Adoption Considerations

### For Compliance Teams
- Define rules in business language; engineering translates to code
- Review and approve the rule registry quarterly
- Audit remediation logs for patterns and emerging risks

### For Engineering Teams
- Integrate compliance scanning as a pipeline stage, not a separate system
- Treat compliance rules like code: version controlled, tested, reviewed
- Build self-healing before manual escalation paths

### For Leadership
- Compliance-by-design reduces review costs by 80%+
- Automated enforcement is more consistent than manual review
- Audit trail is automatic — no additional documentation burden

---

*Compliance-by-design is not about restricting AI — it's about making AI outputs trustworthy by default. When compliance is embedded in the pipeline, the question shifts from "is this output safe?" to "the system guarantees this output is safe."*
