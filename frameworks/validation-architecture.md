# Multi-Layer Validation Architecture

**A 4-layer defense system for AI output validation**

---

## Why Multi-Layer?

Single-layer validation creates a binary: pass or fail. Real-world AI outputs fail in diverse ways — structural issues, compliance violations, quality shortfalls, and factual errors require different detection strategies.

A multi-layer approach:
- Catches different failure types at the appropriate layer
- Enables targeted repair (fix only what's broken)
- Provides granular metrics (which layers catch what)
- Allows per-layer tuning without affecting other layers

---

## The Four Layers

```
┌─────────────────────────────────────────────────┐
│  Layer 4: Hallucination Detection               │
│  "Is this factually grounded?"                  │
├─────────────────────────────────────────────────┤
│  Layer 3: Quality Scoring                       │
│  "Is this good enough for production?"          │
├─────────────────────────────────────────────────┤
│  Layer 2: Compliance Validation                 │
│  "Does this meet regulatory requirements?"      │
├─────────────────────────────────────────────────┤
│  Layer 1: Structural Validation                 │
│  "Is this a well-formed output?"                │
└─────────────────────────────────────────────────┘
```

Each layer has a clear mandate, deterministic where possible, and a defined remediation path.

---

## Layer 1: Structural Validation

**Purpose:** Ensure the AI output is well-formed and contains all expected components.

**Detection method:** Deterministic (100% reliable)

```python
class StructuralValidator:
    """Validate output structure before checking content."""

    def validate(self, output: AIOutput) -> ValidationResult:
        checks = []

        # Required fields present
        for field in output.schema.required_fields:
            checks.append(FieldCheck(
                field=field.name,
                present=field.name in output.data,
                valid_type=isinstance(output.data.get(field.name), field.expected_type)
            ))

        # Length constraints
        for field, constraints in output.schema.length_constraints.items():
            value = output.data.get(field, "")
            checks.append(LengthCheck(
                field=field,
                actual_length=len(value),
                min_length=constraints.min,
                max_length=constraints.max,
                passed=constraints.min <= len(value) <= constraints.max
            ))

        # Format constraints (dates, URLs, identifiers)
        for field, format_rule in output.schema.format_rules.items():
            value = output.data.get(field, "")
            checks.append(FormatCheck(
                field=field,
                expected_format=format_rule.pattern,
                passed=format_rule.matches(value)
            ))

        return ValidationResult(
            layer="STRUCTURAL",
            passed=all(c.passed for c in checks),
            checks=checks,
            remediation="REGENERATE" if not all(c.passed for c in checks) else None
        )
```

**Remediation:** Regenerate the output — structural failures indicate fundamental generation issues.

**Typical catch rate:** 2-5% of outputs fail structural validation.

---

## Layer 2: Compliance Validation

**Purpose:** Ensure the output meets all regulatory and policy requirements.

**Detection method:** Deterministic (rule-based scanning)

```python
class ComplianceValidator:
    """Rule-based compliance validation — zero false negatives for known patterns."""

    def __init__(self):
        self.phrase_detector = BannedPhraseDetector(
            phrases=load_banned_phrases(),  # 500+ phrases across domains
            matching_modes=["exact", "fuzzy", "semantic_pattern"]
        )
        self.disclosure_checker = RequiredDisclosureChecker()
        self.pii_scanner = PIIScanner()

    def validate(self, output: AIOutput) -> ValidationResult:
        violations = []

        # Banned phrase detection
        phrase_hits = self.phrase_detector.scan(output.text)
        for hit in phrase_hits:
            violations.append(ComplianceViolation(
                rule=hit.rule_id,
                text=hit.matched_text,
                regulation=hit.regulation,
                severity=hit.severity,
                auto_fixable=hit.has_safe_replacement
            ))

        # Required disclosures
        missing_disclosures = self.disclosure_checker.find_missing(
            output, output.context
        )
        for disclosure in missing_disclosures:
            violations.append(ComplianceViolation(
                rule=disclosure.rule_id,
                text=f"Missing: {disclosure.name}",
                regulation=disclosure.regulation,
                severity="HIGH",
                auto_fixable=True  # System can insert disclosures
            ))

        # PII leak detection
        pii_findings = self.pii_scanner.scan(output.text)
        for finding in pii_findings:
            violations.append(ComplianceViolation(
                rule="PII_LEAK",
                text=finding.matched_text,
                regulation="DATA_PRIVACY",
                severity="CRITICAL",
                auto_fixable=finding.can_redact
            ))

        return ValidationResult(
            layer="COMPLIANCE",
            passed=len(violations) == 0,
            violations=violations,
            remediation="SELF_HEAL" if all(v.auto_fixable for v in violations)
                       else "REGENERATE"
        )
```

**Remediation:** Self-heal (replace banned phrases, insert disclosures, redact PII). Only regenerate if violations are unfixable.

**Typical catch rate:** 8-15% of outputs have compliance issues (pre-remediation).

---

## Layer 3: Quality Scoring

**Purpose:** Ensure the output meets quality standards — not just "valid" but "good."

**Detection method:** Hybrid (deterministic rules + AI-assisted scoring)

```python
class QualityScorer:
    """Multi-dimensional quality assessment with composite scoring."""

    def __init__(self):
        self.dimensions = {
            "completeness": CompletenessScorer(),    # All key points covered?
            "clarity": ClarityScorer(),              # Clear, readable language?
            "relevance": RelevanceScorer(),           # On-topic, appropriate?
            "originality": OriginalityScorer(),       # Not repetitive or generic?
            "tone": ToneScorer(),                     # Matches intended tone?
        }
        self.thresholds = QualityThresholds.load()

    def score(self, output: AIOutput) -> QualityResult:
        scores = {}

        for dimension, scorer in self.dimensions.items():
            score = scorer.evaluate(output)
            scores[dimension] = DimensionScore(
                value=score.value,          # 0.0 - 1.0
                confidence=score.confidence,
                evidence=score.evidence,    # Why this score?
                threshold=self.thresholds.get(dimension)
            )

        composite = self._compute_composite(scores)

        # Identify weakest dimensions for targeted improvement
        weak_dimensions = [
            dim for dim, score in scores.items()
            if score.value < score.threshold
        ]

        return QualityResult(
            layer="QUALITY",
            composite_score=composite,
            dimension_scores=scores,
            passed=composite >= self.thresholds.minimum_composite,
            weak_dimensions=weak_dimensions,
            remediation="TARGETED_REGEN" if weak_dimensions else None,
            regen_guidance=self._build_regen_guidance(weak_dimensions)
        )

    def _build_regen_guidance(self, weak_dimensions: list) -> dict:
        """Tell the regeneration agent WHAT to improve, not just 'try again'."""
        return {
            dim: self.dimensions[dim].improvement_guidance()
            for dim in weak_dimensions
        }
```

**Remediation:** Targeted regeneration — only re-run the components that scored below threshold, with specific improvement guidance.

**Key insight:** "Try again" is not a remediation strategy. The system must tell the generator *what* to improve.

---

## Layer 4: Hallucination Detection

**Purpose:** Ensure AI-generated claims are grounded in source data.

**Detection method:** AI-assisted with deterministic verification

```python
class HallucinationDetector:
    """Detect claims not supported by source data."""

    def __init__(self):
        self.fact_extractor = FactExtractor()
        self.source_matcher = SourceMatcher()
        self.known_patterns = HallucinationPatternLibrary()

    def detect(self, output: AIOutput, source_data: dict) -> HallucinationResult:
        # Step 1: Extract factual claims from output
        claims = self.fact_extractor.extract(output.text)

        # Step 2: Match each claim against source data
        ungrounded = []
        for claim in claims:
            match = self.source_matcher.find_support(claim, source_data)
            if match.confidence < 0.8:
                ungrounded.append(UngroundedClaim(
                    claim=claim,
                    best_match=match,
                    confidence=match.confidence,
                    category=self._categorize(claim)
                ))

        # Step 3: Check for known hallucination patterns
        pattern_matches = self.known_patterns.scan(output.text)

        # Step 4: Predictive factual routing
        # Route claims through fact-specific validators
        for claim in ungrounded:
            if claim.category == "NUMERIC":
                claim.verified = self._verify_numeric(claim, source_data)
            elif claim.category == "ENTITY":
                claim.verified = self._verify_entity(claim, source_data)
            elif claim.category == "TEMPORAL":
                claim.verified = self._verify_temporal(claim, source_data)

        truly_hallucinated = [c for c in ungrounded if not c.verified]

        return HallucinationResult(
            layer="HALLUCINATION",
            total_claims=len(claims),
            verified_claims=len(claims) - len(truly_hallucinated),
            hallucinated_claims=truly_hallucinated,
            pattern_matches=pattern_matches,
            passed=len(truly_hallucinated) == 0,
            remediation="FACTUAL_REPAIR" if truly_hallucinated else None
        )
```

**Remediation:** Factual grounding repair — replace hallucinated claims with verified facts from source data, or remove claims that cannot be verified.

**Key principle:** The system assumes all AI claims are unverified until matched against source data. Trust is earned, not assumed.

---

## Pipeline Orchestration

```python
class ValidationPipeline:
    """Orchestrate all four validation layers with short-circuit logic."""

    def __init__(self):
        self.layers = [
            StructuralValidator(),
            ComplianceValidator(),
            QualityScorer(),
            HallucinationDetector()
        ]
        self.max_repair_attempts = 3

    def validate(self, output: AIOutput, context: dict) -> PipelineResult:
        attempt = 0
        current_output = output
        layer_results = []

        while attempt < self.max_repair_attempts:
            for layer in self.layers:
                result = layer.validate(current_output)
                layer_results.append(result)

                if not result.passed:
                    # Attempt repair before moving to next layer
                    repaired = self._attempt_repair(
                        current_output, result
                    )

                    if repaired:
                        current_output = repaired
                        # Re-validate from Layer 1 after repair
                        break
                    else:
                        # Cannot repair — return failure
                        return PipelineResult(
                            status="BLOCKED",
                            failing_layer=result.layer,
                            attempts=attempt + 1,
                            layer_results=layer_results
                        )
            else:
                # All layers passed
                return PipelineResult(
                    status="VALIDATED",
                    output=current_output,
                    attempts=attempt + 1,
                    layer_results=layer_results
                )

            attempt += 1

        return PipelineResult(
            status="MAX_ATTEMPTS_EXCEEDED",
            attempts=self.max_repair_attempts,
            layer_results=layer_results
        )
```

---

## The Last Mutation Boundary Rule

One of the most critical lessons from production: **any system with post-processing must enforce final integrity at the LAST mutation boundary, not the first.**

### The Problem

Consider a pipeline: Generation → Compliance Scan → Grammar Repair → Output. If compliance is checked after generation but grammar repair runs after compliance, the grammar repair can **reintroduce violations** that compliance already caught. The fix was validated at the wrong boundary.

### The Rule

> Final integrity enforcement must occur at the **outermost mutation point** — the last place in the pipeline where content can change. Any mutation after a compliance check invalidates that check.

### Dual-Layer Gates

In practice, this means implementing integrity gates at two levels:

```python
class DualLayerIntegrityGate:
    """
    Enforce integrity at both component level and service level.

    Layer 1 (Component): Each content generator enforces its own integrity
    Layer 2 (Service): The service that orchestrates generators enforces
              final integrity AFTER all mutations are complete

    The service-level gate is the authoritative one. The component-level
    gate catches issues early but cannot be trusted as final.
    """

    def enforce_component_level(self, content: str) -> str:
        """First gate — catches most issues early."""
        content = self.compliance_scanner.scan_and_fix(content)
        content = self.quality_enforcer.enforce(content)
        return content

    def enforce_service_level(self, content: str) -> str:
        """
        Final gate — runs AFTER all post-processing is complete.

        This is the authoritative integrity check. If content fails here,
        it is blocked from production regardless of component-level results.
        """
        result = self.final_integrity_check(content)
        if not result.passed:
            # Content failed at the last boundary — block it
            return self._build_deterministic_fallback(content)
        return content
```

### Why This Matters

In production, this pattern eliminated a class of bugs where:
- Grammar repair re-introduced banned phrases after compliance scanning
- Text normalization changed content after quality validation
- Post-processing formatting mutations invalidated prior compliance checks

The principle: **validate at the last moment, not the first.** Anything checked early can be invalidated by later mutations.

---

## Monitoring & Observability

Each layer produces telemetry for governance monitoring:

| Metric | Purpose | Alert Threshold |
|---|---|---|
| Layer 1 failure rate | Structural quality of generation | > 10% |
| Layer 2 violation rate | Compliance drift detection | > 20% |
| Layer 3 mean quality score | Quality trend monitoring | < 0.6 |
| Layer 4 hallucination rate | Factual grounding degradation | > 5% |
| End-to-end pass rate | Overall system health | < 75% |
| Repair success rate | Self-healing effectiveness | < 85% |

---

## Deployment Considerations

### Per-Asset Isolation
Each output is validated independently. One asset failing validation does not block other assets in the same batch. This enables:
- Parallel validation for performance
- Granular status tracking (completed / degraded / blocked)
- Targeted retry without re-processing successful outputs

### Feature Flag Rollout
New validation layers should be deployed behind feature flags:
1. **Shadow mode** — Run new layer, log results, don't enforce
2. **Advisory mode** — Warn on failures, don't block
3. **Enforcement mode** — Block failing outputs

This allows calibration before enforcement, preventing false positives from blocking production.

### Extraction as Critical Infrastructure
If your validation depends on extracting structured data from source material, treat the extraction step as critical infrastructure. Bad extraction poisons all downstream validation. Implement a validation gate on extraction itself — if extraction quality is below threshold, fall back to a safe default rather than validating against bad data.

---

*The goal of multi-layer validation is not to catch every possible failure — it's to make the probability of an undetected failure negligibly small. Each layer reduces risk independently, and their combined effect is multiplicative.*
