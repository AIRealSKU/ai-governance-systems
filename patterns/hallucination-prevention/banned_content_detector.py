"""
Banned Content Detector
=======================

High-performance pattern detection for identifying prohibited content in AI outputs.
Supports exact match, case-insensitive, regex, and contextual pattern matching.

Developed for regulated industries where specific terms, phrases, or patterns
must never appear in AI-generated content (e.g., discriminatory language,
unauthorized disclosures, competitor mentions).

Design decisions:
- Deterministic: No AI in the detection loop — 100% recall for known patterns
- Domain-separated: Each compliance domain manages its own phrase registry
- Performance-optimized: Pre-compiled patterns, early termination on critical finds
- Auditable: Every detection includes the rule that triggered it
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MatchMode(Enum):
    EXACT = "exact"                    # Exact string match
    CASE_INSENSITIVE = "case_insensitive"  # Case-insensitive match
    REGEX = "regex"                    # Regular expression
    WORD_BOUNDARY = "word_boundary"    # Match only at word boundaries
    CONTEXTUAL = "contextual"         # Only a violation in certain contexts


class Severity(Enum):
    CRITICAL = "critical"   # Must block output — legal/regulatory risk
    HIGH = "high"           # Should block — policy violation
    MEDIUM = "medium"       # Should warn — quality concern
    LOW = "low"             # Informational — may need review


class ComplianceDomain(Enum):
    FAIR_HOUSING = "fair_housing"
    FAIR_LENDING = "fair_lending"
    DATA_PRIVACY = "data_privacy"
    ADVERTISING = "advertising"
    ACCESSIBILITY = "accessibility"
    INTERNAL_POLICY = "internal_policy"


@dataclass
class BannedPhrase:
    """A single banned phrase with metadata for detection and remediation."""
    phrase_id: str
    pattern: str
    match_mode: MatchMode
    domain: ComplianceDomain
    severity: Severity
    regulation: str                    # Which regulation requires this
    reason: str                        # Why is this banned?
    safe_alternative: Optional[str] = None  # What to replace with
    context_required: Optional[str] = None  # Only banned in this context
    _compiled: Optional[re.Pattern] = field(default=None, repr=False)

    def compile(self) -> None:
        """Pre-compile regex pattern for performance."""
        if self.match_mode == MatchMode.EXACT:
            self._compiled = re.compile(re.escape(self.pattern))
        elif self.match_mode == MatchMode.CASE_INSENSITIVE:
            self._compiled = re.compile(re.escape(self.pattern), re.IGNORECASE)
        elif self.match_mode == MatchMode.REGEX:
            self._compiled = re.compile(self.pattern, re.IGNORECASE)
        elif self.match_mode == MatchMode.WORD_BOUNDARY:
            self._compiled = re.compile(
                rf"\b{re.escape(self.pattern)}\b", re.IGNORECASE
            )
        elif self.match_mode == MatchMode.CONTEXTUAL:
            self._compiled = re.compile(
                re.escape(self.pattern), re.IGNORECASE
            )


@dataclass
class Detection:
    """A single detection of banned content in AI output."""
    phrase: BannedPhrase
    matched_text: str
    position: int                  # Character position in output
    line_number: int
    context_snippet: str           # Surrounding text for review
    auto_fixable: bool
    fix_suggestion: Optional[str] = None


@dataclass
class ScanResult:
    """Result of scanning an AI output for banned content."""
    clean: bool
    detections: list[Detection]
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    scan_time_ms: float
    phrases_checked: int
    auto_fixable_count: int

    @property
    def total_detections(self) -> int:
        return len(self.detections)

    @property
    def requires_block(self) -> bool:
        """Output must be blocked if any critical or high severity detections."""
        return self.critical_count > 0 or self.high_count > 0


class BannedPhraseRegistry:
    """
    Central registry of all banned phrases across compliance domains.

    In production, this is populated from:
    - Database seed data (500+ phrases)
    - Regulatory updates (periodic refresh)
    - Incident-driven additions (new phrases discovered through audit)
    """

    def __init__(self):
        self.phrases: list[BannedPhrase] = []
        self._by_domain: dict[ComplianceDomain, list[BannedPhrase]] = {}
        self._compiled = False

    def load_domain(self, domain: ComplianceDomain, phrases: list[BannedPhrase]):
        """Load phrases for a specific compliance domain."""
        self.phrases.extend(phrases)
        self._by_domain[domain] = phrases
        self._compiled = False

    def compile_all(self):
        """Pre-compile all patterns for performance."""
        for phrase in self.phrases:
            phrase.compile()
        self._compiled = True

    def get_by_domain(self, domain: ComplianceDomain) -> list[BannedPhrase]:
        return self._by_domain.get(domain, [])

    def get_critical(self) -> list[BannedPhrase]:
        return [p for p in self.phrases if p.severity == Severity.CRITICAL]

    @property
    def total_phrases(self) -> int:
        return len(self.phrases)


class BannedContentDetector:
    """
    High-performance banned content detection engine.

    Scanning strategy:
    1. Critical phrases first (early termination if blocking is needed)
    2. Domain-grouped scanning for cache efficiency
    3. Pre-compiled patterns for regex performance
    4. Context extraction for audit trail
    """

    def __init__(
        self,
        registry: BannedPhraseRegistry,
        context_window: int = 50,       # Characters of context around detection
        early_terminate_on_critical: bool = True,
    ):
        self.registry = registry
        self.context_window = context_window
        self.early_terminate = early_terminate_on_critical

        # Ensure patterns are compiled
        if not registry._compiled:
            registry.compile_all()

    def scan(self, text: str, domains: list[ComplianceDomain] | None = None) -> ScanResult:
        """
        Scan text for all banned content.

        Args:
            text: The AI-generated text to scan
            domains: Optional filter — only check specific domains

        Returns:
            ScanResult with all detections and metadata
        """
        import time
        start = time.monotonic()

        detections: list[Detection] = []
        phrases_to_check = self._get_phrases(domains)

        # Sort: critical first for early termination
        phrases_to_check.sort(
            key=lambda p: list(Severity).index(p.severity)
        )

        # Pre-compute line positions for line number reporting
        line_starts = self._compute_line_starts(text)

        for phrase in phrases_to_check:
            if phrase._compiled is None:
                continue

            for match in phrase._compiled.finditer(text):
                # Context check for contextual patterns
                if phrase.match_mode == MatchMode.CONTEXTUAL:
                    if not self._check_context(text, match, phrase):
                        continue

                detection = Detection(
                    phrase=phrase,
                    matched_text=match.group(),
                    position=match.start(),
                    line_number=self._get_line_number(match.start(), line_starts),
                    context_snippet=self._extract_context(text, match),
                    auto_fixable=phrase.safe_alternative is not None,
                    fix_suggestion=phrase.safe_alternative,
                )
                detections.append(detection)

                # Early termination: if we found a critical violation and
                # caller wants fast feedback, stop scanning
                if (
                    self.early_terminate
                    and phrase.severity == Severity.CRITICAL
                ):
                    break

        elapsed_ms = (time.monotonic() - start) * 1000

        return ScanResult(
            clean=len(detections) == 0,
            detections=detections,
            critical_count=sum(
                1 for d in detections if d.phrase.severity == Severity.CRITICAL
            ),
            high_count=sum(
                1 for d in detections if d.phrase.severity == Severity.HIGH
            ),
            medium_count=sum(
                1 for d in detections if d.phrase.severity == Severity.MEDIUM
            ),
            low_count=sum(
                1 for d in detections if d.phrase.severity == Severity.LOW
            ),
            scan_time_ms=elapsed_ms,
            phrases_checked=len(phrases_to_check),
            auto_fixable_count=sum(1 for d in detections if d.auto_fixable),
        )

    def remediate(self, text: str, detections: list[Detection]) -> str:
        """
        Apply automatic fixes for all auto-fixable detections.

        Applies fixes in reverse position order to preserve character positions.
        """
        # Sort by position descending to maintain positions during replacement
        sorted_detections = sorted(
            [d for d in detections if d.auto_fixable],
            key=lambda d: d.position,
            reverse=True,
        )

        result = text
        for detection in sorted_detections:
            if detection.fix_suggestion:
                result = (
                    result[:detection.position]
                    + detection.fix_suggestion
                    + result[detection.position + len(detection.matched_text):]
                )

        return result

    def _get_phrases(
        self, domains: list[ComplianceDomain] | None
    ) -> list[BannedPhrase]:
        """Get phrases filtered by domain if specified."""
        if domains is None:
            return list(self.registry.phrases)
        phrases = []
        for domain in domains:
            phrases.extend(self.registry.get_by_domain(domain))
        return phrases

    def _compute_line_starts(self, text: str) -> list[int]:
        """Pre-compute line start positions for efficient line number lookup."""
        starts = [0]
        for i, char in enumerate(text):
            if char == "\n":
                starts.append(i + 1)
        return starts

    def _get_line_number(self, position: int, line_starts: list[int]) -> int:
        """Binary search for line number given character position."""
        low, high = 0, len(line_starts) - 1
        while low <= high:
            mid = (low + high) // 2
            if line_starts[mid] <= position:
                low = mid + 1
            else:
                high = mid - 1
        return high + 1  # 1-indexed

    def _extract_context(self, text: str, match: re.Match) -> str:
        """Extract surrounding context for audit trail."""
        start = max(0, match.start() - self.context_window)
        end = min(len(text), match.end() + self.context_window)
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(text) else ""
        return f"{prefix}{text[start:end]}{suffix}"

    def _check_context(
        self, text: str, match: re.Match, phrase: BannedPhrase
    ) -> bool:
        """
        For contextual phrases, check if the surrounding context
        makes this a true violation.

        Example: "master" is only a violation in housing context
        (master bedroom → primary bedroom), not in technical context.
        """
        if not phrase.context_required:
            return True

        context_start = max(0, match.start() - 200)
        context_end = min(len(text), match.end() + 200)
        surrounding = text[context_start:context_end].lower()

        return phrase.context_required.lower() in surrounding


# --- Example: Building a Fair Housing phrase registry ---

def build_fair_housing_registry() -> BannedPhraseRegistry:
    """
    Example: Build a registry for Fair Housing Act compliance.

    In production, this is loaded from a database with 500+ phrases.
    This demonstrates the pattern with representative examples.
    """
    registry = BannedPhraseRegistry()

    fair_housing_phrases = [
        BannedPhrase(
            phrase_id="FH-001",
            pattern="no children",
            match_mode=MatchMode.CASE_INSENSITIVE,
            domain=ComplianceDomain.FAIR_HOUSING,
            severity=Severity.CRITICAL,
            regulation="Fair Housing Act - Familial Status",
            reason="Discriminates based on familial status",
            safe_alternative="",  # Remove entirely
        ),
        BannedPhrase(
            phrase_id="FH-002",
            pattern="perfect for young professionals",
            match_mode=MatchMode.CASE_INSENSITIVE,
            domain=ComplianceDomain.FAIR_HOUSING,
            severity=Severity.HIGH,
            regulation="Fair Housing Act - Familial Status/Age",
            reason="Implies age/family preference",
            safe_alternative="perfect for professionals",
        ),
        BannedPhrase(
            phrase_id="FH-003",
            pattern="walking distance to church",
            match_mode=MatchMode.CASE_INSENSITIVE,
            domain=ComplianceDomain.FAIR_HOUSING,
            severity=Severity.MEDIUM,
            regulation="Fair Housing Act - Religion",
            reason="May imply religious preference",
            safe_alternative="walking distance to local amenities",
        ),
        BannedPhrase(
            phrase_id="FH-004",
            pattern=r"master\s+(bedroom|suite|bath)",
            match_mode=MatchMode.REGEX,
            domain=ComplianceDomain.FAIR_HOUSING,
            severity=Severity.MEDIUM,
            regulation="Fair Housing Act - Race (industry guidance)",
            reason="Industry moving away from 'master' terminology",
            safe_alternative="primary bedroom",
        ),
        BannedPhrase(
            phrase_id="FH-005",
            pattern="exclusive neighborhood",
            match_mode=MatchMode.CASE_INSENSITIVE,
            domain=ComplianceDomain.FAIR_HOUSING,
            severity=Severity.HIGH,
            regulation="Fair Housing Act - Race/National Origin",
            reason="'Exclusive' implies discriminatory selection",
            safe_alternative="desirable neighborhood",
        ),
    ]

    registry.load_domain(ComplianceDomain.FAIR_HOUSING, fair_housing_phrases)
    registry.compile_all()

    return registry
