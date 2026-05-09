"""Submission readiness scoring — 0 to 100."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

from nmtcapp.data.schema import (
    GRADE_THRESHOLDS,
    IMPACT_BENCHMARKS,
    MIN_GEOGRAPHIC_DIVERSITY,
    READINESS_SCORING_WEIGHTS,
    TARGET_DISTRESS_THRESHOLDS,
    ValidationResult,
)

if TYPE_CHECKING:
    from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class ReadinessScore:
    """Submission readiness assessment for a NMTC application.

    Example::

        score = compute_readiness_score(analysis_result, validation_results)
        print(score.summary())
    """
    overall_score: float
    component_scores: dict
    grade: str
    top_strengths: List[str]
    top_weaknesses: List[str]
    recommendations: List[str]

    def summary(self) -> str:
        """Return a formatted readiness report.

        Example::

            print(score.summary())
        """
        bar = _score_bar(self.overall_score)
        lines = [
            "=" * 60,
            f"  APPLICATION READINESS SCORE: {self.overall_score:.1f}/100  [{self.grade}]",
            f"  {bar}",
            "=" * 60,
            "",
            "Component Scores:",
        ]
        for component, score in self.component_scores.items():
            label = component.replace("_", " ").title()
            lines.append(f"  {label:<30} {score:5.1f}/100")
        lines.extend([
            "",
            "Top Strengths:",
            *[f"  + {s}" for s in self.top_strengths],
            "",
            "Areas for Improvement:",
            *[f"  - {w}" for w in self.top_weaknesses],
            "",
            "Recommendations:",
            *[f"  → {r}" for r in self.recommendations],
            "=" * 60,
        ])
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dictionary."""
        return {
            "overall_score": self.overall_score,
            "grade": self.grade,
            "component_scores": self.component_scores,
            "top_strengths": self.top_strengths,
            "top_weaknesses": self.top_weaknesses,
            "recommendations": self.recommendations,
        }


def compute_readiness_score(
    analysis_result: "PipelineAnalysisResult",
    validation_results: List[ValidationResult],
) -> ReadinessScore:
    """Compute a 0–100 readiness score with weighted components.

    Components and weights (see ``READINESS_SCORING_WEIGHTS``):
    - eligibility_quality (0.25)
    - distress_concentration (0.25)
    - geographic_diversity (0.15)
    - impact_metrics (0.20)
    - validation_pass_rate (0.10)
    - completeness (0.05)

    Example::

        score = compute_readiness_score(result, [elig_val, complete_val, consist_val])
        print(score.grade)
    """
    weights = READINESS_SCORING_WEIGHTS

    # --- Component: eligibility quality ---
    eligibility_score = _eligibility_score(analysis_result)

    # --- Component: distress concentration ---
    distress_score = _distress_score(analysis_result)

    # --- Component: geographic diversity ---
    geo_score = _geo_score(analysis_result)

    # --- Component: impact metrics ---
    impact_score = _impact_score(analysis_result)

    # --- Component: validation pass rate ---
    val_score = _validation_score(validation_results)

    # --- Component: completeness ---
    completeness_score = _completeness_score(analysis_result, validation_results)

    component_scores = {
        "eligibility_quality":   round(eligibility_score, 1),
        "distress_concentration": round(distress_score, 1),
        "geographic_diversity":  round(geo_score, 1),
        "impact_metrics":        round(impact_score, 1),
        "validation_pass_rate":  round(val_score, 1),
        "completeness":          round(completeness_score, 1),
    }

    overall = sum(
        component_scores[k] * weights[k] for k in weights
    )
    overall = min(100.0, max(0.0, round(overall, 1)))

    grade = _compute_grade(overall)
    strengths = _identify_strengths(component_scores)
    weaknesses = _identify_weaknesses(component_scores)
    recommendations = _build_recommendations(analysis_result, component_scores, validation_results)

    return ReadinessScore(
        overall_score=overall,
        component_scores=component_scores,
        grade=grade,
        top_strengths=strengths,
        top_weaknesses=weaknesses,
        recommendations=recommendations,
    )


# ---------------------------------------------------------------------------
# Component scorers (each returns 0–100)
# ---------------------------------------------------------------------------

def _eligibility_score(result: "PipelineAnalysisResult") -> float:
    pct = result.eligibility_pct
    if pct >= 0.98:
        return 100.0
    if pct >= 0.90:
        return 75.0 + (pct - 0.90) * 250
    return pct * 80.0


def _distress_score(result: "PipelineAnalysisResult") -> float:
    d = result.distress_breakdown
    pct = d.get("pct_deep_or_severe", 0.0)
    target = TARGET_DISTRESS_THRESHOLDS["target_deep_distress"]
    if pct >= 0.85:
        return 100.0
    if pct >= target:
        return 80.0 + (pct - target) * 200
    if pct >= TARGET_DISTRESS_THRESHOLDS["min_deep_distress"]:
        return 50.0 + (pct - 0.50) * 120
    return pct * 100.0


def _geo_score(result: "PipelineAnalysisResult") -> float:
    g = result.geographic_diversity
    states = g.get("states_count", 0)
    hhi = g.get("hhi", 10_000)
    base = min(100.0, states / MIN_GEOGRAPHIC_DIVERSITY * 50.0)
    diversity_bonus = max(0.0, (5_000 - hhi) / 5_000 * 50.0)
    return min(100.0, base + diversity_bonus)


def _impact_score(result: "PipelineAnalysisResult") -> float:
    i = result.aggregate_impact
    jpm = i.get("jobs_per_million_qei", 0.0)
    high = IMPACT_BENCHMARKS["jobs_per_million_qei_high"]
    avg = IMPACT_BENCHMARKS["jobs_per_million_qei_avg"]
    if jpm >= high:
        return 100.0
    if jpm >= avg:
        return 65.0 + (jpm - avg) / (high - avg) * 35.0
    if jpm > 0:
        return (jpm / avg) * 65.0
    return 0.0


def _validation_score(validation_results: List[ValidationResult]) -> float:
    if not validation_results:
        return 50.0
    total_issues = sum(len(v.issues) for v in validation_results)
    passed = sum(1 for v in validation_results if v.passed)
    pass_rate = passed / len(validation_results)
    # Penalize hard issues more than pass rate
    penalty = min(50.0, total_issues * 10.0)
    return max(0.0, pass_rate * 100.0 - penalty)


def _completeness_score(result: "PipelineAnalysisResult", validation_results: list) -> float:
    for vr in validation_results:
        if vr.check_name == "completeness_check":
            if vr.passed and not vr.warnings:
                return 100.0
            if vr.passed:
                return 80.0
            # Deduct per issue
            return max(0.0, 100.0 - len(vr.issues) * 20.0)
    # No completeness check run — estimate from pipeline data
    if result.total_projects > 0:
        return 75.0
    return 0.0


# ---------------------------------------------------------------------------
# Grade, strengths/weaknesses, recommendations
# ---------------------------------------------------------------------------

def _compute_grade(score: float) -> str:
    if score >= GRADE_THRESHOLDS["A"]:
        return "A"
    if score >= GRADE_THRESHOLDS["B"]:
        return "B"
    if score >= GRADE_THRESHOLDS["C"]:
        return "C"
    if score >= GRADE_THRESHOLDS["D"]:
        return "D"
    return "F"


def _identify_strengths(scores: dict) -> List[str]:
    strengths = []
    if scores["eligibility_quality"] >= 80:
        strengths.append("High pipeline eligibility rate (≥80% score)")
    if scores["distress_concentration"] >= 80:
        strengths.append("Strong deep/severe distress concentration")
    if scores["geographic_diversity"] >= 70:
        strengths.append("Good geographic diversity across multiple states")
    if scores["impact_metrics"] >= 70:
        strengths.append("Above-average jobs/impact per million QEI")
    if scores["validation_pass_rate"] >= 90:
        strengths.append("Clean validation — no blocking issues")
    return strengths[:3] or ["Pipeline established with initial projects"]


def _identify_weaknesses(scores: dict) -> List[str]:
    weaknesses = []
    if scores["distress_concentration"] < 60:
        weaknesses.append("Distress concentration below competitive threshold")
    if scores["geographic_diversity"] < 50:
        weaknesses.append("Geographic footprint too narrow — add more states")
    if scores["impact_metrics"] < 50:
        weaknesses.append("Jobs/impact per million QEI below CDFI Fund average")
    if scores["eligibility_quality"] < 80:
        weaknesses.append("Some projects may not be NMTC-eligible — verify tracts")
    if scores["validation_pass_rate"] < 70:
        weaknesses.append("Validation failures require resolution before submission")
    return weaknesses[:3]


def _build_recommendations(
    result: "PipelineAnalysisResult",
    scores: dict,
    validation_results: list,
) -> List[str]:
    recs = []
    d = result.distress_breakdown
    g = result.geographic_diversity

    if scores["distress_concentration"] < 75:
        current = d.get("pct_deep_or_severe", 0)
        target = TARGET_DISTRESS_THRESHOLDS["target_deep_distress"]
        recs.append(
            f"Increase deep/severe distress concentration from {current:.0%} to ≥{target:.0%} "
            "by substituting standard LIC projects with deeper-distress alternatives"
        )
    if scores["geographic_diversity"] < 60:
        recs.append(
            f"Expand geographic footprint — currently {g.get('states_count', 0)} states. "
            f"Target ≥{MIN_GEOGRAPHIC_DIVERSITY + 2} states for competitive score"
        )
    if scores["impact_metrics"] < 60:
        recs.append(
            "Add operating business projects (manufacturing, healthcare) to improve "
            "jobs-per-million-QEI metric above CDFI Fund average of 12"
        )
    for vr in validation_results:
        for issue in vr.issues[:1]:
            recs.append(f"Resolve validation error: {issue}")

    return recs[:5] or ["Continue strengthening pipeline — add deep-distress projects in target markets"]


def _score_bar(score: float, width: int = 30) -> str:
    filled = int(score / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {score:.1f}%"
