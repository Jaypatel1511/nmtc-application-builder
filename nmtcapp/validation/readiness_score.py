"""Submission readiness scoring — 0 to 100."""
from __future__ import annotations

import logging
import textwrap
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
    # WITHDRAWAL MARKER (1.5.2 T1). ADDITIVE, NOT A REPLACEMENT.
    #
    # ``top_strengths``, ``top_weaknesses`` and ``recommendations`` are public
    # API and are still here, still typed, still in to_dict(). They are now
    # EMPTY of composite-derived narrative. Removing them would be a breaking
    # change and belongs with the 2.0.0 deletion of overall_score/grade; a
    # patch may not do it.
    #
    # These two fields exist because an EMPTY LIST AND A WITHDRAWN ONE READ
    # IDENTICALLY to a JSON consumer, which is the same defect the geographic
    # withdrawal was written to avoid on the rendered surfaces. A caller
    # reading to_dict() can now tell the difference without parsing prose.
    narrative_withdrawn: bool = False
    narrative_note: str = ""

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
        # THE THREE NARRATIVE BLOCKS ARE GONE AND SAY SO (1.5.2 T1). They are
        # not simply omitted: this block stands where they stood, because a
        # CDE who ran the tool last week is looking for them here. Any list
        # that still has content prints under its own heading below.
        if self.top_strengths:
            lines.extend(["", "Top Strengths:",
                          *[f"  + {s}" for s in self.top_strengths]])
        if self.top_weaknesses:
            lines.extend(["", "Areas for Improvement:",
                          *[f"  - {w}" for w in self.top_weaknesses]])
        if self.narrative_note:
            lines.extend(["", *_wrap_note(self.narrative_note)])
        if self.recommendations:
            lines.extend([
                "",
                "Still emitted — NOT derived from the readiness composite:",
                *[f"  → {r}" for r in self.recommendations],
            ])
        lines.append("=" * 60)
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
            "narrative_withdrawn": self.narrative_withdrawn,
            "narrative_note": self.narrative_note,
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
        narrative_withdrawn=True,
        narrative_note=narrative_withdrawal_note(component_scores),
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


#: The readiness composite's own components, in the order summary() prints
#: them, mapped to the house constant each one's band comes from. Stated once
#: so the withdrawal note cannot drift from what the scorers actually read.
_COMPONENT_BASIS = {
    "eligibility_quality":    "this tool's own eligibility curve",
    "distress_concentration": "schema.TARGET_DISTRESS_THRESHOLDS (HOUSE)",
    "geographic_diversity":   "schema.MIN_GEOGRAPHIC_DIVERSITY (HOUSE)",
    "impact_metrics":         "schema.IMPACT_BENCHMARKS (HOUSE)",
    "validation_pass_rate":   "this tool's own pass-rate curve",
    "completeness":           "this tool's own completeness curve",
}


def narrative_withdrawal_note(component_scores: dict) -> str:
    """The ONE statement of the 1.5.2 withdrawal, read by every surface.

    THE WITHDRAWAL, AND WHY IT IS NOT A DELETION (1.5.2 T1)

    ``_identify_strengths``, ``_identify_weaknesses`` and
    ``_build_recommendations`` were the entire mechanism by which a house band
    became an instruction to restructure a real pipeline. They rendered on two
    surfaces: ``ReadinessScore.summary()``, which is what ``nmtcapp analyze``
    prints, and ``renderers/markdown_builder``'s executive summary, which is
    the first page of a generated application document.

    EVERY TRIGGER IN ALL THREE WAS A HOUSE BAND. Not one of them has a CDFI
    Fund referent, and this package's own constant registry
    (tests/pinned_constants.txt) already rules
    ``schema.READINESS_SCORING_WEIGHTS`` an "unsourced house heuristic",
    ``IMPACT_BENCHMARKS`` "this tool's own screening bands" and
    ``TARGET_DISTRESS_THRESHOLDS[target_deep_distress]`` an "internal scoring
    band". The composite they weight is not a Fund score.

    WITHDRAWN, NOT SILENTLY EMPTIED, and the precedent is this package's own.
    1.5.1 withdrew the geographic recommendation out loud because "an absent
    recommendation and a withdrawn one read differently to a CDE who ran the
    tool last week". Emptying three functions without saying so would make the
    whole narrative absent, which is the larger version of the same error.

    AND THE DEDUCTIONS ARE STATED, which is the half that is easy to lose. The
    1.5.1 audit's F4 finding was that withholding advice while keeping the
    deduction silent is worse than either failure alone: the CDE stops being
    warned and keeps being penalised. T1 withdraws advice for ALL SIX
    components, so F4's rule now applies six times over. What replaces the
    advice is therefore not silence but arithmetic — the composite's own
    accounting, in the tool's own terms, instructing nothing.
    """
    weights = READINESS_SCORING_WEIGHTS
    docked = []
    for key, score in component_scores.items():
        if score >= 100:
            continue
        weight = weights[key]
        dock = (100.0 - score) * weight
        label = key.replace("_", " ").title()
        docked.append(
            f"    {label:<26} {score:5.1f}/100 at a {weight:>3.0%} weight  ->  "
            f"DOCKED {dock:.1f} POINTS  [{_COMPONENT_BASIS[key]}]"
        )
    total = sum(
        (100.0 - v) * weights[k] for k, v in component_scores.items() if v < 100
    )

    lines = [
        "READINESS NARRATIVE WITHDRAWN (1.5.2). This tool no longer emits "
        "strengths, weaknesses or recommendations from the readiness "
        "composite, and none are offered in this release.",
        "",
        "WHAT WAS WITHDRAWN. Earlier versions read this composite's "
        "sub-scores and told a CDE to act on them: to increase deep/severe "
        "distress concentration to a target share, to add operating-business "
        "projects to raise a jobs-per-$1MM-QEI figure, and (withdrawn "
        "separately in 1.5.1) to expand its footprint to >=5 states. They "
        "also asserted strengths and weaknesses -- that a share was 'above "
        "average', that a concentration was 'below competitive threshold'.",
        "",
        # THE NOTE CARRIES ITS OWN DISCLOSURE ANCHOR, DELIBERATELY. This
        # paragraph names "readiness score", which is a readiness CLAIM under
        # tests/test_pinned_constants._READINESS_CLAIM, and the proximity gate
        # measures every such claim against the nearest recognised readiness
        # disclosure. Naming the composite "this tool's own unsourced house
        # heuristic" in the same sentence satisfies that gate at ~50
        # characters instead of weakening it -- and it is the accurate
        # description, not a token planted to pass.
        "WHY. EVERY ONE OF THOSE TRIGGERS WAS A BAND THIS TOOL SET FOR "
        "ITSELF. The composite they weight is this tool's own unsourced "
        "house heuristic: the CDFI Fund publishes no readiness score, no "
        "such weighting and no grade, so none of the thresholds that fired "
        "those lines has a federal referent -- they are recorded HOUSE in "
        "this package's own constant registry. Restructuring a real pipeline is an "
        "expensive and sometimes irreversible act, and it was being "
        "instructed by arithmetic with nothing behind it. The measured case "
        "is on the record: following the withdrawn geographic advice moved a "
        "sample pipeline from Highly Qualified to Not Qualified under the "
        "Fund's own gate while this tool's grade did not change letter.",
        "",
        "YOU WERE NEVERTHELESS DOCKED, AND HERE IS THE ARITHMETIC. A tool may "
        "decline to advise. It may not deduct silently.",
    ]
    if docked:
        lines += ["", *docked, "",
                  f"    TOTAL DEDUCTION {total:.1f} POINTS of the 100-point "
                  f"readiness headline."]
    else:
        lines += ["", "    No component was docked on this run."]
    lines += [
        "",
        "NONE OF THAT IS A FINDING ABOUT YOUR APPLICATION. The deduction is "
        "this tool's own bookkeeping against its own bands. In particular the "
        "CDFI Fund does not score geographic breadth at all, so nothing in "
        "the headline's geographic term has a federal referent; do not treat "
        "this pipeline's footprint as a finding either way, and do not expand "
        "it to recover those points.",
        "",
        "WHERE THE SOURCED GUIDANCE IS. "
        "`intelligence.RecommendationEngine` is untouched. It never reads "
        "this composite -- it scores against the CY 2024-2025 NMTC Program "
        "Review Process and cites the section behind every item it emits. "
        "Reach it with `Application.recommendations()` in Python, or open "
        "the Win Alignment Scorer page in the Streamlit app.",
        "",
        # THE SILENCE IS SHIPPED OUT LOUD (1.5.2 T1). Mapped before writing
        # this: of the surfaces that carried readiness narrative, NEITHER
        # reaches RecommendationEngine. No renderer imports it, and cli.py
        # does not either -- `nmtcapp analyze` calls analysis.summary() and
        # nothing else. So withdrawing here leaves both surfaces with no
        # improvement guidance at all, and a note that pointed at the sourced
        # engine without saying it is somewhere else would read as though the
        # guidance below had simply moved down the page.
        "IT IS NOT REACHED FROM HERE. Neither `nmtcapp analyze` nor the "
        "generated application documents run that engine, so neither now "
        "carries improvement guidance of any kind. That gap is stated rather "
        "than shipped quietly: reaching the sourced guidance is a separate "
        "call you have to make yourself.",
    ]
    return "\n".join(lines)


def _identify_strengths(scores: dict, geographic_diversity: dict | None = None) -> List[str]:
    """WITHDRAWN (1.5.2 T1). Returns no strengths, on any pipeline.

    WHAT STOOD HERE. Five band-triggered assertions: eligibility >=80,
    distress >=80, geographic >=70 (guarded against the concentration
    contradiction in 1.5.1 T5), impact >=70, validation >=90 -- plus a
    fallback, ``["Pipeline established with initial projects"]``, that fired
    when none of the five did and asserted a quality over a pipeline that had
    cleared no band at all.

    EVERY CUT POINT WAS THIS TOOL'S OWN. 1.5.1 F4 had already established the
    asymmetry that makes praise the more dangerous half -- "a CDE has no
    reason to go looking behind good news" -- and answered it by attaching the
    house basis to each strength. That was the right fix for a line that had
    to keep rendering. It does not have to keep rendering.

    THE ARGUMENT AGAINST WITHDRAWING THIS, STATED. A tool so hedged it emits
    no signal is a failure and not a safe default, and a CDE reading a grade
    with nothing attached is the mirror defect. The answer is not to keep an
    unsourced compliment: it is that the composite's own deduction accounting
    now renders in its place (see :func:`narrative_withdrawal_note`), which is
    strictly more information than "High pipeline eligibility rate" and
    instructs nothing.

    NOT DELETED. The function stays, and stays called, because
    ``top_strengths`` is public API that a 2.0.0 deletion removes and a patch
    may not.
    """
    return []


def _identify_weaknesses(scores: dict) -> List[str]:
    """WITHDRAWN (1.5.2 T1). Returns no weaknesses, on any pipeline.

    WHAT STOOD HERE. Six band-triggered verdicts, including "Distress
    concentration below competitive threshold" -- the word "competitive" being
    a claim about how the CDFI Fund ranks applications, attached to
    ``TARGET_DISTRESS_THRESHOLDS``, which this package's registry rules an
    internal scoring band. That is the T4 defect in prose: a competitiveness
    claim with no Fund referent.

    THE ELIGIBILITY-DATA LINE IS NOT LOST. "Eligibility data unavailable --
    tracts and distress levels unverified" was the one entry here that was not
    a band comparison, and it is stated three other ways already: the ``!!!!``
    banner at the top of :meth:`ReadinessScore.summary`, ``partial_note``, and
    the Streamlit error block. Nothing about it reached a CDE only through
    this list.
    """
    return []


def _build_recommendations(
    result: "PipelineAnalysisResult",
    scores: dict,
    validation_results: list,
) -> List[str]:
    """WITHDRAWN IN PART (1.5.2 T1) -- every band-triggered instruction goes.

    WHAT WAS WITHDRAWN, and each was an instruction to change a real pipeline:

      * ``distress_concentration < 75`` -> "Increase deep/severe distress
        concentration from X% to >=75% by substituting standard LIC projects
        with deeper-distress alternatives". The 75 is
        ``TARGET_DISTRESS_THRESHOLDS[target_deep_distress]``, registry-ruled
        HOUSE, and the share it compares is denominated in QEI while the
        Fund's own commitment is denominated in QLICIs.
      * ``geographic_diversity < 100`` -> the 1.5.1 withdrawal notice. Its
        content is preserved and generalised in
        :func:`narrative_withdrawal_note`, including the deduction arithmetic
        that F4 required, so nothing that round established is dropped here.
      * ``impact_metrics < 60`` -> "Add operating business projects
        (manufacturing, healthcare)...". ``IMPACT_BENCHMARKS`` is registry-
        ruled HOUSE and the 1.2.0 primary-source pass established that the
        publication its numbers once cited does not exist.
      * the ``or [...]`` fallback -> "Continue strengthening pipeline -- add
        deep-distress projects in target markets", which fired when the five
        branches above produced nothing and instructed a pipeline that had
        triggered no band at all.

    WHAT IS RETAINED, AND WHY IT IS NOT THE SAME CLASS. Two emitters here
    never read ``component_scores``:

      * the degraded-data notice, whose trigger is that eligibility data could
        not be loaded. That is a fact about this run, not a comparison against
        a band, and its instruction is to fix the tool's own data access.
      * the validation-issue echo, whose text is an issue string produced by
        the validation checks and already printed in full above it. Its
        referent is the check that raised it.

    Retaining these is deliberate and is the answer to the mirror defect: a
    surface that says only "withdrawn" gives a CDE nothing, and these two
    items are the ones on this surface that were never house-band-derived.
    """
    recs = []

    if "distress_concentration" not in scores:
        recs.append(
            "Restore eligibility data access (nmtc-mapper) and re-run the "
            "analysis — eligibility and distress cannot be verified right now"
        )
    for vr in validation_results:
        for issue in vr.issues[:1]:
            recs.append(f"Resolve validation error: {issue}")

    return recs[:5]


def _wrap_note(note: str, width: int = 76) -> List[str]:
    """Wrap the withdrawal note for the fixed-width CLI block.

    Lines that are already indented are pre-formatted (the deduction table)
    and pass through untouched -- rewrapping them would destroy the column
    alignment that makes the arithmetic readable.
    """
    out = []
    for para in note.split("\n"):
        if not para.strip():
            out.append("")
        elif para.startswith("    "):
            out.append(f"  {para}")
        else:
            out.extend(f"  {line}" for line in textwrap.wrap(para, width=width))
    return out


def _score_bar(score: float, width: int = 30) -> str:
    filled = int(score / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {score:.1f}%"
