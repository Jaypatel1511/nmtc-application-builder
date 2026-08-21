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
    # Partial-score marker: True when eligibility data was unavailable and the
    # eligibility_quality / distress_concentration components were excluded.
    partial: bool = False
    partial_note: str = ""
    eligibility_data_error: str = ""

    def summary(self) -> str:
        """Return a formatted readiness report.

        Example::

            print(score.summary())
        """
        bar = _score_bar(self.overall_score)
        lines = []
        if self.partial:
            if self.eligibility_data_error:
                lines.extend([
                    "!" * 60,
                    "  ELIGIBILITY DATA UNAVAILABLE",
                    f"  {self.eligibility_data_error}",
                    f"  {self.partial_note}",
                    "!" * 60,
                ])
            else:
                lines.extend([
                    "!" * 60,
                    "  UNVERIFIED PROJECTS IN PIPELINE",
                    f"  {self.partial_note}",
                    "!" * 60,
                ])
        lines += [
            "=" * 60,
            f"  APPLICATION READINESS SCORE: {self.overall_score:.1f}/100  [{self.grade}]"
            + ("  (PARTIAL)" if self.partial else ""),
            f"  {bar}",
        ]
        if self.partial:
            lines.append(f"  {self.partial_note}")
        lines += [
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
            "partial": self.partial,
            "partial_note": self.partial_note,
            "eligibility_data_error": self.eligibility_data_error,
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
    degraded = getattr(analysis_result, "eligibility_data_status", "ok") != "ok"
    unverified_ids = list(getattr(analysis_result, "unverified_project_ids", []) or [])

    # --- Component: geographic diversity ---
    geo_score = _geo_score(analysis_result)

    # --- Component: impact metrics ---
    impact_score = _impact_score(analysis_result)

    # --- Component: validation pass rate ---
    val_score = _validation_score(validation_results)

    # --- Component: completeness ---
    completeness_score = _completeness_score(analysis_result, validation_results)

    component_scores = {
        "geographic_diversity":  round(geo_score, 1),
        "impact_metrics":        round(impact_score, 1),
        "validation_pass_rate":  round(val_score, 1),
        "completeness":          round(completeness_score, 1),
    }

    if not degraded:
        # Eligibility-dependent components only exist when live data was used
        component_scores = {
            "eligibility_quality":   round(_eligibility_score(analysis_result), 1),
            "distress_concentration": round(_distress_score(analysis_result), 1),
            **component_scores,
        }

    # Weights renormalized over the computed components, so a degraded score
    # is still 0–100 but over 4 of 6 components (and labeled as such).
    active_weight = sum(weights[k] for k in component_scores)
    overall = sum(
        component_scores[k] * weights[k] for k in component_scores
    ) / active_weight if active_weight > 0 else 0.0
    overall = min(100.0, max(0.0, round(overall, 1)))

    grade = _compute_grade(overall)
    strengths = _identify_strengths(component_scores, analysis_result.geographic_diversity)
    weaknesses = _identify_weaknesses(component_scores)
    recommendations = _build_recommendations(analysis_result, component_scores, validation_results)

    # Partial marker: degraded (no eligibility data at all) OR any project
    # left unverified — including ALL projects unverified while the pipeline
    # status is still "ok" (the dataset loaded but nothing could be verified).
    partial = degraded or bool(unverified_ids)
    partial_note = ""
    if degraded:
        partial_note = (
            f"score computed without eligibility verification "
            f"({len(component_scores)} of {len(weights)} components)"
        )
    elif unverified_ids:
        partial_note = (
            f"{len(unverified_ids)} projects unverified — locations could not "
            "be verified; eligibility-dependent components are lower bounds "
            "(unverified projects count in the denominator, never the numerator)"
        )

    return ReadinessScore(
        overall_score=overall,
        component_scores=component_scores,
        grade=grade,
        top_strengths=strengths,
        top_weaknesses=weaknesses,
        recommendations=recommendations,
        partial=partial,
        partial_note=partial_note,
        eligibility_data_error=getattr(analysis_result, "eligibility_data_error", None) or "",
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


def _identify_strengths(scores: dict, geographic_diversity: dict | None = None) -> List[str]:
    strengths = []
    if scores.get("eligibility_quality", 0) >= 80:
        strengths.append("High pipeline eligibility rate (≥80% score)")
    if scores.get("distress_concentration", 0) >= 80:
        strengths.append("Strong deep/severe distress concentration")
    # A DIVERSITY CLAIM MAY NOT CONTRADICT THE CONCENTRATION MEASURE ONE BLOCK
    # ABOVE IT (1.5.1 T5). The sub-score is
    # ``min(100, states / MIN_GEOGRAPHIC_DIVERSITY * 50) + hhi_bonus``, whose
    # first term reaches 100 at six states. So from five states upward the
    # state count alone clears this 70 gate and the HHI term is inert — and
    # this line asserted "Good geographic diversity" over a pipeline that
    # geographic_analysis._concentration_label had already printed as
    # ``highly_concentrated`` in the same document. Measured on 1.5.0: six
    # states at HHI 9,519 (one state holding ~97.5% of QEI) scored 100.0 and
    # emitted this strength.
    #
    # THE CURVE IS NOT RE-BASED HERE, DELIBERATELY. Re-basing it is calibration
    # against MIN_GEOGRAPHIC_DIVERSITY, a constant this package already records
    # as HOUSE and underived; replacing one unsourced shape with another is
    # methodology, and it would move every existing user's score on a patch.
    # What is wrong TODAY and fixable today is the tool telling a CDE it has
    # something the tool's own measure says it does not have. The score is
    # unchanged; only the false sentence is withheld.
    #
    # ONE DIRECTION CAVEATED, THE OTHER NOT (1.5.1 audit, F4). T5 fixed the
    # contradiction and T1 rewrote the WEAKNESS to say "this tool's own house
    # curve -- not a CDFI Fund threshold". This line, the mirror of it, was
    # left reading "Good geographic diversity across multiple states":
    # unqualified, in the tool's own voice, asserting a quality. The round
    # withdrew the stick and kept the carrot, and an uncaveated praise is the
    # more dangerous half -- a CDE has no reason to go looking behind good
    # news. Both halves now carry the same basis, because they are scored by
    # the same unsourced curve.
    _concentrated = (geographic_diversity or {}).get(
        "geographic_concentration_label"
    ) == "highly_concentrated"
    if scores["geographic_diversity"] >= 70 and not _concentrated:
        strengths.append(
            "High geographic-diversity sub-score on this tool's own house "
            "curve — not a CDFI Fund threshold, and not a finding about the "
            "application"
        )
    if scores["impact_metrics"] >= 70:
        # NOT "Above-average". That claimed a comparison against an external
        # average — IMPACT_BENCHMARKS["jobs_per_million_qei_avg"], a constant
        # whose provenance is a section comment, not a citation. Same defect
        # as impact_aggregator._benchmark_label, one layer up, and it rendered
        # into the Key Strengths list on the first page. The threshold here is
        # this tool's own, so the line now says so.
        strengths.append(
            "Jobs and units per $1MM QEI clear this tool's impact-score threshold"
        )
    if scores["validation_pass_rate"] >= 90:
        strengths.append("Clean validation — no blocking issues")
    return strengths[:3] or ["Pipeline established with initial projects"]


def _identify_weaknesses(scores: dict) -> List[str]:
    weaknesses = []
    if "eligibility_quality" not in scores:
        weaknesses.append(
            "Eligibility data unavailable — tracts and distress levels unverified"
        )
    if scores.get("distress_concentration", 100) < 60:
        weaknesses.append("Distress concentration below competitive threshold")
    if scores["geographic_diversity"] < 50:
        # THE SECOND HALF OF T1, AND IT WAS NOT ON THE LIST. This read
        # "Geographic footprint too narrow — add more states", which is the
        # suppressed recommendation in a shorter sentence: "too narrow" is a
        # verdict against a bar the CDFI Fund does not set, and "add more
        # states" is the same instruction, on the surface a CDE reads FIRST.
        # Withdrawing the recommendation while leaving this here would have
        # withdrawn the paragraph and kept the advice.
        #
        # What survives is the measurement, which is true and is this tool's
        # own: the sub-score is low. What is withheld is the verdict and the
        # instruction.
        weaknesses.append(
            "Low geographic-diversity sub-score on this tool's own house "
            "curve — not a CDFI Fund threshold, and not a finding about the "
            "application"
        )
    if scores["impact_metrics"] < 50:
        weaknesses.append(
            "Jobs and units per $1MM QEI below this tool's impact-score band"
        )
    if scores.get("eligibility_quality", 100) < 80:
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

    if "distress_concentration" not in scores:
        recs.append(
            "Restore eligibility data access (nmtc-mapper) and re-run the "
            "analysis — eligibility and distress cannot be verified right now"
        )
    if scores.get("distress_concentration", 100) < 75:
        current = d.get("pct_deep_or_severe", 0)
        target = TARGET_DISTRESS_THRESHOLDS["target_deep_distress"]
        recs.append(
            f"Increase deep/severe distress concentration from {current:.0%} to ≥{target:.0%} "
            "by substituting standard LIC projects with deeper-distress alternatives"
        )
    # THE TRIGGER IS ANY DEDUCTION, NOT A BAND (1.5.1 audit, F4). This read
    # ``< 60``, which left a hole the round did not see: a FOUR-state pipeline
    # scores 66.7 on this curve, clears both the ``< 60`` notice here and the
    # ``< 50`` weakness above, and is told NOTHING about geography -- while
    # being docked 4.99 points of the 100-point readiness headline it is shown.
    #
    # MEASURED, not reasoned: geo 66.7 costs (100 - 66.7) * 0.15 = 4.99. The
    # pipeline sees a lower grade and no reason for it anywhere in strengths,
    # weaknesses or recommendations.
    #
    # THAT IS THE FAILURE MODE SUPPRESSION PRODUCES, and it is worse than
    # either half alone: the CDE stops being warned and keeps being penalised.
    # A tool may decline to advise. It may not deduct silently. So the trigger
    # is now "this component cost you points" -- the only honest condition --
    # and the notice states the size of the deduction.
    if scores["geographic_diversity"] < 100:
        # WITHDRAWN, NOT DROPPED (1.5.1 T1). This slot rendered "Expand
        # geographic footprint — currently N states. Target ≥5 states…" and it
        # fired on exactly the pipelines that were already clearing the CDFI
        # Fund's own gate.
        #
        # MEASURED ON 1.5.0, not reasoned. A pipeline of two states at 100%
        # deep/severe distress scores Community Outcomes 44/50, aggregate
        # 94 — Highly Qualified. Its geographic sub-score is 33.3, so this
        # recommendation fired. Following it to five states dilutes distress:
        # at 55% deep the aggregate falls to 89 and the tier flips to Not
        # Qualified, while the readiness headline moves 83.0 [B] to 82.0 [B].
        # THE GRADE DOES NOT CHANGE ACROSS THE FUND'S GATE. A CDE watching the
        # number this tool prints largest would see nothing happen while its
        # application stopped qualifying.
        #
        # The Review Process scores no state count — schema.py says so at
        # MIN_GEOGRAPHIC_DIVERSITY, and the CY 2024-2025 Allocation Application
        # asks for a service area, not a minimum number of states. So this was
        # the one recommendation in either engine pointing at a metric the Fund
        # does not score, in a direction that costs points on metrics it does.
        #
        # SUPPRESSION, NOT CORRECTION, because writing the right advice means
        # deriving what geographic breadth is worth — the recommendation-engine
        # methodology, which is the next round. Suppression is reversible; the
        # harm direction is not. The withdrawal is stated out loud because an
        # absent recommendation and a withdrawn one read differently to a CDE
        # who ran this tool last week.
        #
        # NOT SUPPRESSED: intelligence/recommendations.RecommendationEngine,
        # which emits no geographic advice at all and cites the Review Process
        # section behind every item it does emit. A CDE is not left without
        # guidance here.
        _geo_sub = scores["geographic_diversity"]
        _dock = (100.0 - _geo_sub) * READINESS_SCORING_WEIGHTS[
            "geographic_diversity"
        ]
        recs.append(
            "Geographic-footprint guidance is WITHDRAWN pending a methodology "
            "review and is not offered in this release. Earlier versions "
            "advised expanding to ≥5 states to raise this tool's "
            "geographic-diversity sub-score; the CDFI Fund scores no state "
            "count, and following that advice can dilute deep/severe distress "
            "concentration, which the Fund does score. "
            # THE DEDUCTION IS STATED (audit F4). Withholding the advice while
            # keeping the deduction silent is the worse of the two failures.
            f"YOU WERE NEVERTHELESS DOCKED {_dock:.1f} POINTS of the "
            "100-point readiness headline for this: "
            f"the geographic-diversity sub-score is {_geo_sub:.1f}/100 and "
            f"carries a {READINESS_SCORING_WEIGHTS['geographic_diversity']:.0%} "
            "weight in a total that is itself this tool's own unsourced "
            "heuristic. That deduction is NOT evidence your footprint is a "
            "problem — the CDFI Fund does not score geographic breadth at all, "
            "so nothing in the readiness headline's geographic term has a "
            "federal referent. Do not treat this pipeline's "
            f"{g.get('states_count', 0)}-state footprint as a finding either "
            "way, and do not expand it to recover these points. See the "
            "CY 2024-2025 Review Process, Community Outcomes, for what is "
            "actually scored"
        )
    if scores["impact_metrics"] < 60:
        recs.append(
            "Add operating business projects (manufacturing, healthcare) to improve "
            "jobs-per-million-QEI metric above this tool's 12 FTE screening "
            "band (a house band, not a CDFI Fund figure)"
        )
    for vr in validation_results:
        for issue in vr.issues[:1]:
            recs.append(f"Resolve validation error: {issue}")

    return recs[:5] or ["Continue strengthening pipeline — add deep-distress projects in target markets"]


def _score_bar(score: float, width: int = 30) -> str:
    filled = int(score / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {score:.1f}%"
