"""
Output Quality Scoring
======================

Multi-dimensional quality assessment for AI-generated outputs.

Instead of a single pass/fail, this system provides:
- Per-dimension scores (completeness, clarity, originality, etc.)
- Composite score with configurable weighting
- Threshold enforcement with targeted improvement guidance
- Trend tracking for system health monitoring

Key health metric: First-pass clean rate
- The percentage of outputs that pass all quality checks on first generation
- ≥ 25% is healthy (system is well-tuned)
- < 15% is danger zone (prompts or model need attention)
- This is NOT about making every output perfect on first try —
  it's about the system trending in the right direction

Design decisions:
- Dimensions are independently scored — one weak dimension doesn't
  mask strengths in others
- Improvement guidance is specific — "improve clarity" is not actionable,
  "reduce sentence length in paragraph 3" is
- Quality thresholds are configurable per content type — a social post
  has different standards than a legal document
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class QualityDimension(Enum):
    COMPLETENESS = "completeness"      # All required elements present?
    CLARITY = "clarity"                # Clear, readable, well-structured?
    RELEVANCE = "relevance"            # On-topic, appropriate for context?
    ORIGINALITY = "originality"        # Not generic, templated, or repetitive?
    TONE = "tone"                      # Matches intended voice/style?
    ACCURACY = "accuracy"              # Factually correct? (overlaps with hallucination)
    DENSITY = "density"                # Appropriate information density?
    ENGAGEMENT = "engagement"          # Compelling, interesting to read?


@dataclass
class DimensionScore:
    """Score for a single quality dimension."""
    dimension: QualityDimension
    score: float                       # 0.0 - 1.0
    confidence: float                  # How confident is this score?
    threshold: float                   # Minimum acceptable score
    evidence: list[str]                # Why this score?
    improvement_hints: list[str]       # Specific improvement suggestions

    @property
    def passed(self) -> bool:
        return self.score >= self.threshold

    @property
    def gap(self) -> float:
        """How far below threshold? 0 if above."""
        return max(0, self.threshold - self.score)


@dataclass
class QualityThresholds:
    """Configurable thresholds per content type."""
    content_type: str
    minimum_composite: float = 0.65
    dimension_minimums: dict[QualityDimension, float] = field(
        default_factory=lambda: {
            QualityDimension.COMPLETENESS: 0.7,
            QualityDimension.CLARITY: 0.6,
            QualityDimension.RELEVANCE: 0.7,
            QualityDimension.ORIGINALITY: 0.5,
            QualityDimension.TONE: 0.5,
            QualityDimension.ACCURACY: 0.8,
            QualityDimension.DENSITY: 0.5,
            QualityDimension.ENGAGEMENT: 0.4,
        }
    )
    dimension_weights: dict[QualityDimension, float] = field(
        default_factory=lambda: {
            QualityDimension.COMPLETENESS: 0.20,
            QualityDimension.CLARITY: 0.15,
            QualityDimension.RELEVANCE: 0.15,
            QualityDimension.ORIGINALITY: 0.15,
            QualityDimension.TONE: 0.10,
            QualityDimension.ACCURACY: 0.15,
            QualityDimension.DENSITY: 0.05,
            QualityDimension.ENGAGEMENT: 0.05,
        }
    )


@dataclass
class QualityResult:
    """Complete quality assessment result."""
    composite_score: float
    dimension_scores: dict[QualityDimension, DimensionScore]
    passed: bool
    weak_dimensions: list[QualityDimension]
    improvement_plan: list[str]
    content_type: str
    is_first_pass_clean: bool          # Passed on first attempt?
    generation_attempt: int = 1

    @property
    def strong_dimensions(self) -> list[QualityDimension]:
        return [
            dim for dim, score in self.dimension_scores.items()
            if score.passed
        ]

    def get_regen_guidance(self) -> dict:
        """
        Build specific guidance for regeneration.

        Instead of "try again", tell the generator exactly what to improve.
        """
        guidance = {}
        for dim in self.weak_dimensions:
            score = self.dimension_scores[dim]
            guidance[dim.value] = {
                "current_score": score.score,
                "target_score": score.threshold,
                "gap": score.gap,
                "hints": score.improvement_hints,
            }
        return guidance


class CompletenessScorer:
    """Score how completely the output covers required elements."""

    def score(self, output: str, requirements: dict) -> DimensionScore:
        required_elements = requirements.get("required_elements", [])
        if not required_elements:
            return DimensionScore(
                dimension=QualityDimension.COMPLETENESS,
                score=1.0,
                confidence=0.9,
                threshold=0.7,
                evidence=["No required elements specified"],
                improvement_hints=[],
            )

        found = 0
        missing = []
        for element in required_elements:
            if self._element_present(output, element):
                found += 1
            else:
                missing.append(element)

        score = found / len(required_elements)

        return DimensionScore(
            dimension=QualityDimension.COMPLETENESS,
            score=score,
            confidence=0.85,
            threshold=0.7,
            evidence=[
                f"Found {found}/{len(required_elements)} required elements",
                *(f"Missing: {m}" for m in missing),
            ],
            improvement_hints=[
                f"Include {element}" for element in missing
            ],
        )

    def _element_present(self, output: str, element: str) -> bool:
        """Check if a required element is present in the output."""
        return element.lower() in output.lower()


class ClarityScorer:
    """Score readability and structural clarity."""

    def score(self, output: str) -> DimensionScore:
        scores = []
        hints = []
        evidence = []

        # Sentence length analysis
        sentences = [s.strip() for s in output.split(".") if s.strip()]
        if sentences:
            avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_length > 25:
                scores.append(0.4)
                hints.append(
                    f"Average sentence length is {avg_length:.0f} words — "
                    "aim for under 20"
                )
            elif avg_length > 20:
                scores.append(0.6)
                hints.append("Some sentences could be shorter for readability")
            else:
                scores.append(0.9)
            evidence.append(f"Average sentence length: {avg_length:.0f} words")

        # Paragraph structure
        paragraphs = [p.strip() for p in output.split("\n\n") if p.strip()]
        if len(paragraphs) == 1 and len(output) > 500:
            scores.append(0.3)
            hints.append("Break content into multiple paragraphs")
        else:
            scores.append(0.8)
        evidence.append(f"Paragraph count: {len(paragraphs)}")

        # Jargon density (simplified check)
        word_count = len(output.split())
        if word_count > 0:
            long_words = sum(1 for w in output.split() if len(w) > 12)
            jargon_ratio = long_words / word_count
            if jargon_ratio > 0.15:
                scores.append(0.5)
                hints.append("Reduce technical jargon for broader readability")
            else:
                scores.append(0.8)
            evidence.append(f"Complex word ratio: {jargon_ratio:.1%}")

        avg_score = sum(scores) / len(scores) if scores else 0.5

        return DimensionScore(
            dimension=QualityDimension.CLARITY,
            score=avg_score,
            confidence=0.7,
            threshold=0.6,
            evidence=evidence,
            improvement_hints=hints,
        )


class OriginalityScorer:
    """Score whether output avoids generic, templated, or repetitive content."""

    GENERIC_OPENERS = [
        "in today's",
        "in the world of",
        "when it comes to",
        "it's no secret that",
        "as we all know",
        "in this day and age",
        "at the end of the day",
        "it goes without saying",
    ]

    def score(self, output: str) -> DimensionScore:
        evidence = []
        hints = []
        penalties = 0.0

        output_lower = output.lower()

        # Generic opener detection
        for opener in self.GENERIC_OPENERS:
            if opener in output_lower:
                penalties += 0.1
                hints.append(f"Replace generic opener: '{opener}'")
                evidence.append(f"Generic opener found: '{opener}'")

        # Repetition detection (repeated phrases)
        words = output_lower.split()
        if len(words) > 20:
            # Check for repeated 3-word phrases
            trigrams = [
                " ".join(words[i : i + 3]) for i in range(len(words) - 2)
            ]
            repeated = {t for t in trigrams if trigrams.count(t) > 2}
            if repeated:
                penalties += 0.15 * len(repeated)
                for phrase in list(repeated)[:3]:
                    hints.append(f"Repeated phrase: '{phrase}'")
                evidence.append(f"Found {len(repeated)} repeated phrases")

        score = max(0.0, min(1.0, 1.0 - penalties))

        return DimensionScore(
            dimension=QualityDimension.ORIGINALITY,
            score=score,
            confidence=0.65,
            threshold=0.5,
            evidence=evidence or ["No originality issues detected"],
            improvement_hints=hints,
        )


class DensityScorer:
    """
    Score information density — appropriate detail level for content type.

    Density routing: Different content types need different density levels.
    - Rich source data → 5 paragraphs of detail
    - Medium data → 3 paragraphs
    - Sparse data → 1-2 paragraphs (don't pad with filler)

    Key insight: Density routing doesn't transfer between content types.
    A social post and a detailed report from the same source data need
    completely different density treatments.
    """

    def score(
        self,
        output: str,
        source_data_richness: str = "medium",  # rich / medium / sparse
        content_type: str = "general",
    ) -> DimensionScore:
        word_count = len(output.split())
        paragraphs = len([p for p in output.split("\n\n") if p.strip()])

        # Expected ranges by content type and data richness
        expectations = self._get_expectations(content_type, source_data_richness)

        evidence = [
            f"Word count: {word_count}",
            f"Paragraphs: {paragraphs}",
            f"Expected range: {expectations['min_words']}-{expectations['max_words']} words",
        ]
        hints = []

        # Score based on whether output matches expected density
        if word_count < expectations["min_words"]:
            score = 0.4
            hints.append(
                f"Output is too sparse ({word_count} words). "
                f"Expected at least {expectations['min_words']} for {source_data_richness} data."
            )
        elif word_count > expectations["max_words"]:
            score = 0.5
            hints.append(
                f"Output is too dense ({word_count} words). "
                f"Expected at most {expectations['max_words']}. Trim filler content."
            )
        else:
            score = 0.85

        return DimensionScore(
            dimension=QualityDimension.DENSITY,
            score=score,
            confidence=0.75,
            threshold=0.5,
            evidence=evidence,
            improvement_hints=hints,
        )

    def _get_expectations(
        self, content_type: str, richness: str
    ) -> dict:
        """Get word count expectations based on content type and data richness."""
        defaults = {
            "rich": {"min_words": 200, "max_words": 600, "paragraphs": 5},
            "medium": {"min_words": 100, "max_words": 400, "paragraphs": 3},
            "sparse": {"min_words": 50, "max_words": 200, "paragraphs": 2},
        }
        return defaults.get(richness, defaults["medium"])


class QualityScorer:
    """
    Orchestrates multi-dimensional quality scoring.

    Produces a composite score with per-dimension breakdown,
    targeted improvement guidance for failing dimensions, and
    trend data for monitoring system health.
    """

    def __init__(self, thresholds: Optional[QualityThresholds] = None):
        self.thresholds = thresholds or QualityThresholds(content_type="general")
        self.completeness = CompletenessScorer()
        self.clarity = ClarityScorer()
        self.originality = OriginalityScorer()
        self.density = DensityScorer()

    def score(
        self,
        output: str,
        requirements: dict | None = None,
        source_data_richness: str = "medium",
        generation_attempt: int = 1,
    ) -> QualityResult:
        """
        Score an AI output across all quality dimensions.

        Returns a complete quality assessment with:
        - Per-dimension scores and evidence
        - Composite weighted score
        - Pass/fail determination
        - Targeted improvement plan for failing dimensions
        """
        requirements = requirements or {}
        dimension_scores = {}

        # Score each dimension
        dimension_scores[QualityDimension.COMPLETENESS] = self.completeness.score(
            output, requirements
        )
        dimension_scores[QualityDimension.CLARITY] = self.clarity.score(output)
        dimension_scores[QualityDimension.ORIGINALITY] = self.originality.score(output)
        dimension_scores[QualityDimension.DENSITY] = self.density.score(
            output, source_data_richness
        )

        # Apply thresholds
        for dim, score in dimension_scores.items():
            if dim in self.thresholds.dimension_minimums:
                score.threshold = self.thresholds.dimension_minimums[dim]

        # Compute weighted composite
        composite = 0.0
        total_weight = 0.0
        for dim, score in dimension_scores.items():
            weight = self.thresholds.dimension_weights.get(dim, 0.1)
            composite += score.score * weight
            total_weight += weight

        if total_weight > 0:
            composite /= total_weight

        # Identify weak dimensions
        weak = [
            dim for dim, score in dimension_scores.items()
            if not score.passed
        ]

        # Build improvement plan
        improvement_plan = []
        for dim in weak:
            score = dimension_scores[dim]
            for hint in score.improvement_hints:
                improvement_plan.append(f"[{dim.value}] {hint}")

        passed = composite >= self.thresholds.minimum_composite and not any(
            dim_score.gap > 0.3 for dim_score in dimension_scores.values()
        )

        return QualityResult(
            composite_score=composite,
            dimension_scores=dimension_scores,
            passed=passed,
            weak_dimensions=weak,
            improvement_plan=improvement_plan,
            content_type=self.thresholds.content_type,
            is_first_pass_clean=passed and generation_attempt == 1,
            generation_attempt=generation_attempt,
        )


class FirstPassCleanRateTracker:
    """
    Track first-pass clean rate as a system health indicator.

    This metric measures what percentage of AI outputs pass all
    quality checks on the first generation attempt — without
    needing repair or regeneration.

    Health thresholds:
    - ≥ 25%: Healthy — system is well-tuned
    - 15-25%: Attention needed — review prompts and model config
    - < 15%: Danger zone — systemic quality issue

    This is tracked over time to detect:
    - Quality regression after model updates
    - Prompt degradation
    - Data quality issues in source inputs
    """

    def __init__(self):
        self.total_generations: int = 0
        self.first_pass_clean: int = 0
        self.daily_stats: dict[str, dict] = {}

    def record(self, result: QualityResult):
        """Record a generation result."""
        self.total_generations += 1
        if result.is_first_pass_clean:
            self.first_pass_clean += 1

        today = str(datetime.now().date())
        if today not in self.daily_stats:
            self.daily_stats[today] = {"total": 0, "clean": 0}
        self.daily_stats[today]["total"] += 1
        if result.is_first_pass_clean:
            self.daily_stats[today]["clean"] += 1

    @property
    def clean_rate(self) -> float:
        if self.total_generations == 0:
            return 0.0
        return self.first_pass_clean / self.total_generations

    @property
    def health_status(self) -> str:
        rate = self.clean_rate
        if rate >= 0.25:
            return "HEALTHY"
        elif rate >= 0.15:
            return "ATTENTION"
        else:
            return "DANGER"
