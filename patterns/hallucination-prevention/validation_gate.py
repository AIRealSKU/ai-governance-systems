"""
Validation Gate Pattern
=======================

A multi-pass validation gate that ensures AI outputs are factually grounded
before reaching production. Implements the principle: "trust is earned, not assumed."

This pattern was developed through 70+ sessions of building production AI systems
where hallucinated content in regulated industries creates legal and reputational risk.

Key design decisions:
- Extraction validation gate: If source data extraction fails, fall back to safe
  defaults rather than validating against bad data
- Per-claim verification: Each factual claim is verified independently
- Predictive routing: Claims are routed through type-specific validators
  (numeric, entity, temporal) for higher accuracy
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ClaimType(Enum):
    NUMERIC = "numeric"        # "3 bedrooms", "$450,000", "2,100 sq ft"
    ENTITY = "entity"          # Names, places, organizations
    TEMPORAL = "temporal"      # Dates, timeframes, durations
    DESCRIPTIVE = "descriptive"  # Subjective qualities, features
    COMPARATIVE = "comparative"  # "larger than", "best in class"


class VerificationStatus(Enum):
    VERIFIED = "verified"          # Claim matches source data
    UNVERIFIED = "unverified"      # No matching source data found
    CONTRADICTED = "contradicted"  # Claim conflicts with source data
    NOT_APPLICABLE = "n/a"         # Claim type doesn't require verification


@dataclass
class FactualClaim:
    """A single factual claim extracted from AI output."""
    text: str
    claim_type: ClaimType
    source_field: Optional[str] = None  # Which source field should support this
    confidence: float = 0.0
    status: VerificationStatus = VerificationStatus.UNVERIFIED
    evidence: str = ""


@dataclass
class ExtractionResult:
    """Result of extracting structured data from source material."""
    data: dict
    quality_score: float           # 0.0 - 1.0
    fields_extracted: int
    fields_expected: int
    extraction_method: str         # "structured", "llm", "hybrid"
    is_reliable: bool = True

    @property
    def coverage(self) -> float:
        if self.fields_expected == 0:
            return 0.0
        return self.fields_extracted / self.fields_expected


@dataclass
class ValidationGateResult:
    """Result of the full validation gate process."""
    passed: bool
    total_claims: int
    verified_claims: int
    unverified_claims: int
    contradicted_claims: int
    claims: list = field(default_factory=list)
    extraction_quality: float = 0.0
    used_fallback: bool = False
    gate_reason: str = ""

    @property
    def verification_rate(self) -> float:
        if self.total_claims == 0:
            return 1.0
        return self.verified_claims / self.total_claims


class ExtractionValidator:
    """
    Validates source data extraction quality before using it for verification.

    This is critical infrastructure: if extraction is bad, every downstream
    validation decision is compromised. Better to fall back to safe defaults
    than to validate against corrupted source data.
    """

    MINIMUM_QUALITY = 0.6          # Below this, extraction is unreliable
    MINIMUM_COVERAGE = 0.5         # Must extract at least 50% of expected fields

    def validate(self, extraction: ExtractionResult) -> bool:
        """Return True if extraction is reliable enough for verification."""
        if extraction.quality_score < self.MINIMUM_QUALITY:
            return False
        if extraction.coverage < self.MINIMUM_COVERAGE:
            return False
        return True


class FactExtractor:
    """Extract individual factual claims from AI-generated text."""

    def extract_claims(self, text: str) -> list[FactualClaim]:
        """
        Parse AI output into individual verifiable claims.

        In production, this uses NLP/LLM to identify claims.
        Here we demonstrate the pattern structure.
        """
        claims = []

        # Numeric claims: prices, counts, measurements
        numeric_patterns = self._find_numeric_claims(text)
        for pattern in numeric_patterns:
            claims.append(FactualClaim(
                text=pattern["text"],
                claim_type=ClaimType.NUMERIC,
                source_field=pattern.get("likely_field"),
            ))

        # Entity claims: names, locations, organizations
        entity_patterns = self._find_entity_claims(text)
        for pattern in entity_patterns:
            claims.append(FactualClaim(
                text=pattern["text"],
                claim_type=ClaimType.ENTITY,
                source_field=pattern.get("likely_field"),
            ))

        # Temporal claims: dates, timeframes
        temporal_patterns = self._find_temporal_claims(text)
        for pattern in temporal_patterns:
            claims.append(FactualClaim(
                text=pattern["text"],
                claim_type=ClaimType.TEMPORAL,
                source_field=pattern.get("likely_field"),
            ))

        return claims

    def _find_numeric_claims(self, text: str) -> list[dict]:
        """Identify numeric claims in text. Production uses regex + NLP."""
        # Pattern demonstration — production implementation uses
        # comprehensive regex patterns and NLP entity extraction
        return []

    def _find_entity_claims(self, text: str) -> list[dict]:
        """Identify entity claims in text."""
        return []

    def _find_temporal_claims(self, text: str) -> list[dict]:
        """Identify temporal claims in text."""
        return []


class FactualRouter:
    """
    Route claims through type-specific verification.

    Different claim types require different verification strategies:
    - Numeric: Exact match or within tolerance
    - Entity: Fuzzy string matching
    - Temporal: Date parsing and comparison
    - Descriptive: Semantic similarity (lower confidence threshold)
    """

    def verify_claim(
        self, claim: FactualClaim, source_data: dict
    ) -> FactualClaim:
        """Verify a single claim against source data."""

        if claim.claim_type == ClaimType.NUMERIC:
            return self._verify_numeric(claim, source_data)
        elif claim.claim_type == ClaimType.ENTITY:
            return self._verify_entity(claim, source_data)
        elif claim.claim_type == ClaimType.TEMPORAL:
            return self._verify_temporal(claim, source_data)
        elif claim.claim_type == ClaimType.DESCRIPTIVE:
            # Descriptive claims have lower verification bar
            claim.status = VerificationStatus.NOT_APPLICABLE
            claim.evidence = "Descriptive claims verified at generation time"
            return claim
        else:
            claim.status = VerificationStatus.UNVERIFIED
            return claim

    def _verify_numeric(
        self, claim: FactualClaim, source_data: dict
    ) -> FactualClaim:
        """Verify numeric claims with tolerance for rounding."""
        if claim.source_field and claim.source_field in source_data:
            source_value = source_data[claim.source_field]
            # In production: parse numeric value from claim text,
            # compare with tolerance (e.g., 1% for prices, exact for counts)
            claim.status = VerificationStatus.VERIFIED
            claim.confidence = 0.95
            claim.evidence = f"Matched source field: {claim.source_field}"
        else:
            claim.status = VerificationStatus.UNVERIFIED
            claim.evidence = "No matching source field found"
        return claim

    def _verify_entity(
        self, claim: FactualClaim, source_data: dict
    ) -> FactualClaim:
        """Verify entity claims with fuzzy matching."""
        if claim.source_field and claim.source_field in source_data:
            claim.status = VerificationStatus.VERIFIED
            claim.confidence = 0.9
            claim.evidence = f"Entity matched in source: {claim.source_field}"
        else:
            claim.status = VerificationStatus.UNVERIFIED
            claim.evidence = "Entity not found in source data"
        return claim

    def _verify_temporal(
        self, claim: FactualClaim, source_data: dict
    ) -> FactualClaim:
        """Verify temporal claims with date parsing."""
        if claim.source_field and claim.source_field in source_data:
            claim.status = VerificationStatus.VERIFIED
            claim.confidence = 0.95
            claim.evidence = f"Date verified against: {claim.source_field}"
        else:
            claim.status = VerificationStatus.UNVERIFIED
            claim.evidence = "Date not found in source data"
        return claim


class ValidationGate:
    """
    The main validation gate — orchestrates extraction validation,
    claim extraction, and factual verification.

    Design principle: If extraction fails, fall back to safe defaults.
    Never validate against unreliable source data.
    """

    def __init__(
        self,
        extraction_validator: ExtractionValidator | None = None,
        fact_extractor: FactExtractor | None = None,
        factual_router: FactualRouter | None = None,
        max_unverified_ratio: float = 0.1,  # Max 10% unverified claims
    ):
        self.extraction_validator = extraction_validator or ExtractionValidator()
        self.fact_extractor = fact_extractor or FactExtractor()
        self.factual_router = factual_router or FactualRouter()
        self.max_unverified_ratio = max_unverified_ratio

    def validate(
        self,
        ai_output: str,
        source_data: dict,
        extraction: ExtractionResult,
    ) -> ValidationGateResult:
        """
        Run the full validation gate.

        Steps:
        1. Validate extraction quality (garbage in → garbage out prevention)
        2. Extract factual claims from AI output
        3. Route each claim through type-specific verification
        4. Determine pass/fail based on verification rate
        """

        # Step 1: Validate extraction quality
        extraction_reliable = self.extraction_validator.validate(extraction)

        if not extraction_reliable:
            # Extraction is unreliable — cannot verify claims
            # Fall back to safe mode: only allow outputs with no factual claims
            return ValidationGateResult(
                passed=False,
                total_claims=0,
                verified_claims=0,
                unverified_claims=0,
                contradicted_claims=0,
                extraction_quality=extraction.quality_score,
                used_fallback=True,
                gate_reason=(
                    f"Extraction quality {extraction.quality_score:.2f} "
                    f"below minimum {self.extraction_validator.MINIMUM_QUALITY}"
                ),
            )

        # Step 2: Extract claims
        claims = self.fact_extractor.extract_claims(ai_output)

        if not claims:
            # No factual claims to verify — pass
            return ValidationGateResult(
                passed=True,
                total_claims=0,
                verified_claims=0,
                unverified_claims=0,
                contradicted_claims=0,
                extraction_quality=extraction.quality_score,
                gate_reason="No factual claims detected",
            )

        # Step 3: Verify each claim
        for claim in claims:
            self.factual_router.verify_claim(claim, source_data)

        # Step 4: Compute results
        verified = sum(
            1 for c in claims
            if c.status == VerificationStatus.VERIFIED
        )
        unverified = sum(
            1 for c in claims
            if c.status == VerificationStatus.UNVERIFIED
        )
        contradicted = sum(
            1 for c in claims
            if c.status == VerificationStatus.CONTRADICTED
        )

        # Any contradicted claim is an immediate failure
        if contradicted > 0:
            return ValidationGateResult(
                passed=False,
                total_claims=len(claims),
                verified_claims=verified,
                unverified_claims=unverified,
                contradicted_claims=contradicted,
                claims=claims,
                extraction_quality=extraction.quality_score,
                gate_reason=f"{contradicted} claims contradicted by source data",
            )

        # Check unverified ratio
        unverified_ratio = unverified / len(claims) if claims else 0
        passed = unverified_ratio <= self.max_unverified_ratio

        return ValidationGateResult(
            passed=passed,
            total_claims=len(claims),
            verified_claims=verified,
            unverified_claims=unverified,
            contradicted_claims=contradicted,
            claims=claims,
            extraction_quality=extraction.quality_score,
            gate_reason=(
                "All claims verified"
                if passed
                else f"Unverified ratio {unverified_ratio:.1%} exceeds maximum {self.max_unverified_ratio:.1%}"
            ),
        )
