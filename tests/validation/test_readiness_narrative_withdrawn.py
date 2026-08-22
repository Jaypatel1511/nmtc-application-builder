"""T1 (1.5.2) — the readiness composite emits no narrative, on any pipeline.

WHAT WAS WITHDRAWN, AND WHY IT NEEDED A GATE OF ITS OWN

``_identify_strengths``, ``_identify_weaknesses`` and ``_build_recommendations``
were the entire mechanism by which a band this tool set for itself became an
instruction to restructure a real pipeline. They reached a CDE on two surfaces:
``ReadinessScore.summary()``, printed by ``nmtcapp analyze``, and
``renderers/markdown_builder``'s executive summary — the first page of a
generated application document.

Every trigger in all three was a house band. ``tests/pinned_constants.txt``
rules ``READINESS_SCORING_WEIGHTS`` an "unsourced house heuristic",
``IMPACT_BENCHMARKS`` "this tool's own screening bands" and
``TARGET_DISTRESS_THRESHOLDS[target_deep_distress]`` an "internal scoring
band"; ``MIN_GEOGRAPHIC_DIVERSITY``'s own comment records that the CY 2024-2025
Review Process scores no state count.

THE COVERAGE PROBLEM THIS MODULE EXISTS TO SOLVE, AND IT IS WORSE THAN 1.5.1'S

1.5.1's F2 finding was that both shipped readiness fixtures score geographic
diversity above 70, so two withdrawn branches were never entered by any test.
This round found the same failure one level deeper and affecting twice as much
ground:

    ``nmtc_mapper`` IS NOT INSTALLED IN THIS SUITE'S ENVIRONMENT.

A pipeline built through ``Application.analyze()`` therefore runs the DEGRADED
path — ``eligibility_data_status != "ok"`` — and ``compute_readiness_score``
emits FOUR components, not six: ``eligibility_quality`` and
``distress_concentration`` are absent from ``component_scores`` entirely, so
``_identify_strengths``'s eligibility and distress branches and
``_build_recommendations``'s distress branch cannot be entered at all.

STATED PRECISELY, BECAUSE THE STRONGER VERSION OF THIS SENTENCE IS FALSE. It is
not true that no fixture in the suite reaches six components. Two modules force
the status — ``tests/test_rendered_output_baseline`` and
``tests/test_invariant_output`` both set ``pipeline.eligibility_data_status =
"ok"`` on purpose — and ``conftest``'s ``sample_pipeline_result`` is hand-built
with ``eligibility_pct=1.0``. What is true is narrower and is the part that
matters: those first two are CORPUS gates that compare a rendered document to a
stored baseline, which is precisely the instrument 1.5.1's F2 found insufficient
("a round whose entire subject was disclosure shipped disclosures that no test
rendered"), and a baseline diff is not an assertion about these three
functions.

So this module drives BOTH paths deliberately: pipelines through
``Application.analyze()`` for the degraded four, and hand-built
``PipelineAnalysisResult`` objects — the same construction ``conftest``'s
``sample_pipeline_result`` uses — for the full six. Measured, not assumed:
restoring ``_identify_strengths``'s eligibility branch turns SIX of this
module's cases red and leaves every ``pipeline:`` case green.

Every band is asserted, so a fixture that stops reaching its branch fails here
rather than going quietly vacuous.
"""
from __future__ import annotations

import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.data.schema import (
    IMPACT_BENCHMARKS,
    READINESS_SCORING_WEIGHTS,
    TARGET_DISTRESS_THRESHOLDS,
    ValidationResult,
)
from nmtcapp.intelligence.pipeline_analyzer import PipelineAnalysisResult
from nmtcapp.validation.readiness_score import compute_readiness_score


# ---------------------------------------------------------------------------
# Fixtures — path A: real pipelines (degraded, four components)
# ---------------------------------------------------------------------------

def _project(index, state, qei, distress, jobs):
    return PipelineProject(
        project_id=f"NW-{index:03d}",
        project_name=f"Withdrawal Fixture {index}",
        qalicb_name=f"Withdrawal QALICB {index} LLC",
        address=f"{index} Fixture St",
        city="Fixture City",
        state=state,
        sector="healthcare",
        project_type="operating_business",
        total_project_cost=int(qei * 1.4),
        qei_request=qei,
        qlici_amount=qei,
        expected_jobs_created=jobs,
        expected_jobs_retained=0,
        census_tract="17031010100",
        is_nmtc_eligible=True,
        distress_level=distress,
        is_native_area=False,
        is_high_migration_rural=False,
        is_opportunity_zone=False,
    )


def _score_from_pipeline(spec):
    projects = [_project(i, *args) for i, args in enumerate(spec)]
    app = Application(
        cde=CDEProfile.sample(),
        requested_allocation=sum(p.qei_request for p in projects),
    )
    app.add_pipeline(Pipeline(projects=projects))
    analysis = app.analyze()
    return compute_readiness_score(
        analysis.pipeline_result, analysis.validation_results
    )


#: (state, qei, distress_level, jobs). Chosen so the four live components span
#: their full range: one pipeline under every old cut, one over every one.
_PIPELINE_SHAPES = {
    "everything_low":  [("IL", 10_000_000, "lic", 1)] * 4,
    "everything_high": [(s, 10_000_000, "deep", 400) for s in
                        ("IL", "OH", "MI", "IN", "WI", "MN", "TX", "CA")],
    "middling":        [(s, 10_000_000, "severe", 60) for s in
                        ("IL", "OH", "MI")],
}


# ---------------------------------------------------------------------------
# Fixtures — path B: hand-built results (full six components)
# ---------------------------------------------------------------------------

def _result(eligibility_pct, pct_deep_or_severe, states, hhi, jobs_per_mm):
    """A PipelineAnalysisResult with eligibility data PRESENT.

    Built directly rather than through Application.analyze() because
    nmtc_mapper is absent here and every analysed pipeline is degraded. This
    is the only route to the eligibility_quality and distress_concentration
    branches, and without it half the withdrawal is untested.
    """
    return PipelineAnalysisResult(
        total_projects=8,
        total_qei_request=80_000_000,
        total_project_cost=112_000_000,
        eligibility_pct=eligibility_pct,
        distress_breakdown={
            "pct_deep_or_severe": pct_deep_or_severe,
            "pct_deep": pct_deep_or_severe / 2,
            "pct_lic": 1.0 - pct_deep_or_severe,
            "pct_non_lic": 0.0,
        },
        geographic_diversity={
            "states_count": states,
            "hhi": hhi,
            "geographic_concentration_label": (
                "highly_concentrated" if hhi >= 2_500 else "diversified"
            ),
        },
        sector_mix={},
        aggregate_impact={"jobs_per_million_qei": jobs_per_mm},
        deal_economics_summary={},
    )


#: Every one of these lands under a cut that used to fire a line.
_RESULT_SHAPES = {
    "low_eligibility":  _result(0.55, 0.90, 8, 900, 30.0),
    "low_distress":     _result(1.00, 0.20, 8, 900, 30.0),
    "low_impact":       _result(1.00, 0.90, 8, 900, 0.5),
    "all_high":         _result(1.00, 0.95, 8, 900, 40.0),
}

_PASSING = [ValidationResult("completeness_check", True, [], [])]
_FAILING = [
    ValidationResult("completeness_check", False, ["Missing qei_request"], []),
    ValidationResult("eligibility_check", False, ["Tract 26163515700 is not a LIC"], []),
]


# ---------------------------------------------------------------------------
# The coverage claim
# ---------------------------------------------------------------------------

def test_the_degraded_path_is_what_pipeline_fixtures_actually_exercise():
    """FAIL CLOSED on the finding that motivated path B.

    If nmtc_mapper ever becomes installable in this environment, these
    fixtures stop being degraded and path B stops being the ONLY route to two
    of the six components. That is a good change and it must not happen
    silently, because the reason path B exists would no longer hold and the
    docstring above would be wrong.
    """
    score = _score_from_pipeline(_PIPELINE_SHAPES["middling"])
    assert score.partial, (
        "an analysed pipeline is no longer partial, so nmtc_mapper is now "
        "available. Re-read this module's premise: the degraded path may no "
        "longer be what an unforced Application.analyze() produces."
    )
    assert set(score.component_scores) == {
        "geographic_diversity", "impact_metrics",
        "validation_pass_rate", "completeness",
    }, score.component_scores


def test_the_hand_built_fixtures_reach_every_band_that_used_to_fire():
    """FAIL CLOSED. The bands are asserted, not assumed.

    Each cut named here is the one the withdrawn line was triggered by, read
    off the constant rather than retyped, so re-basing a constant moves this
    claim with it.
    """
    scores = {
        label: compute_readiness_score(result, _PASSING).component_scores
        for label, result in _RESULT_SHAPES.items()
    }
    for label, components in scores.items():
        assert len(components) == 6, (
            f"{label} produced {len(components)} components; the hand-built "
            "results are supposed to carry eligibility data."
        )

    # _identify_strengths' eligibility branch (>= 80) and _identify_weaknesses'
    # (< 80), from opposite sides.
    assert scores["low_eligibility"]["eligibility_quality"] < 80, scores
    assert scores["all_high"]["eligibility_quality"] >= 80, scores

    # _build_recommendations' distress branch (< 75) and the strength (>= 80).
    assert scores["low_distress"]["distress_concentration"] < 75, scores
    assert scores["all_high"]["distress_concentration"] >= 80, scores

    # _build_recommendations' impact branch (< 60) and the strength (>= 70).
    assert scores["low_impact"]["impact_metrics"] < 60, scores
    assert scores["all_high"]["impact_metrics"] >= 70, scores

    # And the constants those cuts are about are still the house ones, so a
    # reader can check the claim above against the registry.
    assert TARGET_DISTRESS_THRESHOLDS["target_deep_distress"] == 0.75
    assert IMPACT_BENCHMARKS["jobs_per_million_qei_avg"] > 0


def test_the_pipeline_fixtures_reach_both_ends_of_the_live_components():
    """FAIL CLOSED for path A, the same way."""
    low = _score_from_pipeline(_PIPELINE_SHAPES["everything_low"]).component_scores
    high = _score_from_pipeline(_PIPELINE_SHAPES["everything_high"]).component_scores
    assert low["geographic_diversity"] < 50, low
    assert low["impact_metrics"] < 50, low
    assert high["geographic_diversity"] >= 70, high
    assert high["impact_metrics"] >= 70, high


# ---------------------------------------------------------------------------
# The withdrawal itself
# ---------------------------------------------------------------------------

def _every_score():
    for label, spec in _PIPELINE_SHAPES.items():
        yield f"pipeline:{label}", _score_from_pipeline(spec)
    for label, result in _RESULT_SHAPES.items():
        yield f"result:{label}", compute_readiness_score(result, _PASSING)
        yield f"result:{label}+failures", compute_readiness_score(result, _FAILING)


#: Every instruction the three functions used to emit, in the shape a
#: reversion would restore it. Matched case-insensitively against the union of
#: all three lists.
_WITHDRAWN_INSTRUCTIONS = (
    "increase deep/severe distress concentration",
    "substituting standard lic projects",
    "add operating business projects",
    "expand geographic footprint",
    "continue strengthening pipeline",
    "add deep-distress projects in target markets",
    "high pipeline eligibility rate",
    "strong deep/severe distress concentration",
    "good geographic diversity",
    "above-average",
    "below competitive threshold",
    "geographic footprint too narrow",
    "add more states",
    "clean validation",
    "pipeline established with initial projects",
)


@pytest.mark.parametrize("label,score", list(_every_score()),
                         ids=lambda v: v if isinstance(v, str) else "")
def test_the_composite_emits_no_narrative(label, score):
    """T1. No strength, no weakness, and no band-triggered recommendation.

    Proved red by restoring one instruction: putting the impact recommendation
    back into ``_build_recommendations`` fails this on every fixture whose
    impact sub-score is under 60.
    """
    assert score.top_strengths == [], (
        f"{label}: the composite emitted strength(s). Every trigger in "
        f"_identify_strengths was a house band:\n  {score.top_strengths}"
    )
    assert score.top_weaknesses == [], (
        f"{label}: the composite emitted weakness(es):\n  {score.top_weaknesses}"
    )

    emitted = " || ".join(
        list(score.top_strengths) + list(score.top_weaknesses)
        + list(score.recommendations)
    ).lower()
    offenders = [p for p in _WITHDRAWN_INSTRUCTIONS if p in emitted]
    assert not offenders, (
        f"{label}: the readiness composite emitted withdrawn instruction(s) "
        f"{offenders}.\n\nThese are triggered by bands this tool set for "
        "itself; the CDFI Fund publishes no readiness score, no such "
        "weighting and no grade.\n\nEmitted:\n"
        + "\n".join(f"  - {s}" for s in
                    list(score.top_strengths) + list(score.top_weaknesses)
                    + list(score.recommendations))
    )


@pytest.mark.parametrize("label,score", list(_every_score()),
                         ids=lambda v: v if isinstance(v, str) else "")
def test_every_surviving_recommendation_is_sourced_outside_the_composite(label, score):
    """The mirror defect. Withdrawal must not become indiscriminate silence.

    Two emitters in ``_build_recommendations`` never read ``component_scores``
    — the degraded-data notice and the validation-issue echo — and both are
    deliberately retained. This asserts that what survives is EXACTLY those
    two, so a future edit cannot smuggle a band-triggered line back in under
    the heading that says these are not composite-derived.
    """
    for text in score.recommendations:
        assert (
            text.startswith("Resolve validation error: ")
            or text.startswith("Restore eligibility data access")
        ), (
            f"{label}: a surviving recommendation is neither a validation-issue "
            f"echo nor the degraded-data notice:\n  {text}"
        )


def test_the_validation_echo_actually_survives_on_a_failing_pipeline():
    """NON-VACUITY for the test above, which passes trivially on an empty list.

    If the retained emitters stopped firing, every assertion about "what
    survives" would be about nothing, and the claim that T1 left a sourced
    signal in place would be false while green.
    """
    score = compute_readiness_score(_RESULT_SHAPES["all_high"], _FAILING)
    echoes = [r for r in score.recommendations
              if r.startswith("Resolve validation error: ")]
    assert len(echoes) == 2, (
        "the validation-issue echo no longer fires on a pipeline with two "
        f"failing checks. Recommendations: {score.recommendations}"
    )
    assert "26163515700" in " ".join(echoes), echoes


def test_the_degraded_notice_survives_and_is_not_a_band(): 
    """The other retained emitter, on the path that produces it."""
    score = _score_from_pipeline(_PIPELINE_SHAPES["middling"])
    assert any(r.startswith("Restore eligibility data access")
               for r in score.recommendations), score.recommendations


# ---------------------------------------------------------------------------
# Withdrawn, not silently emptied
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("label,score", list(_every_score()),
                         ids=lambda v: v if isinstance(v, str) else "")
def test_the_withdrawal_is_stated_not_implied(label, score):
    """An absent narrative and a withdrawn one must not read the same.

    This package's own precedent, from the 1.5.1 geographic withdrawal: "an
    absent recommendation and a withdrawn one read differently to a CDE who
    ran the tool last week."
    """
    assert score.narrative_withdrawn is True, label
    note = score.narrative_note
    assert "WITHDRAWN" in note, f"{label}: {note[:200]}"

    for required in (
        # what was withdrawn
        "strengths", "weaknesses", "recommendations", "Earlier versions",
        # whose bands they were
        "publishes no readiness score", "no such weighting and no grade",
        "this tool's own unsourced",
        # where the sourced guidance is
        "RecommendationEngine", "Review Process",
        "Application.recommendations()",
        # and that neither withdrawing surface reaches it
        "IT IS NOT REACHED FROM HERE",
    ):
        assert required in note, (
            f"{label}: the withdrawal note omits {required!r}. A note that "
            "does not say what was withdrawn, whose bands it rested on, or "
            "where the sourced guidance is, is an absence with a header.\n\n"
            + note
        )


@pytest.mark.parametrize("label,score", list(_every_score()),
                         ids=lambda v: v if isinstance(v, str) else "")
def test_no_component_is_docked_silently(label, score):
    """F4's rule, now binding on all six components rather than on geography.

    "A tool may decline to advise. It may not deduct silently." T1 withdraws
    advice for every component, so every DOCKED component must appear in the
    note's arithmetic with its own deduction.
    """
    note = score.narrative_note
    docked = {k: v for k, v in score.component_scores.items() if v < 100}
    if not docked:
        assert "No component was docked" in note, note
        return

    total = 0.0
    for key, value in docked.items():
        weight = READINESS_SCORING_WEIGHTS[key]
        dock = (100.0 - value) * weight
        total += dock
        pretty = key.replace("_", " ").title()
        assert pretty in note, (
            f"{label}: {pretty} scored {value} and cost "
            f"{dock:.1f} points, and the note never names it:\n{note}"
        )
        assert f"DOCKED {dock:.1f} POINTS" in note, (
            f"{label}: the note does not state {pretty}'s deduction of "
            f"{dock:.1f} points:\n{note}"
        )
    assert f"TOTAL DEDUCTION {total:.1f} POINTS" in note, (
        f"{label}: the note does not state the total deduction of "
        f"{total:.1f} points:\n{note}"
    )


# ---------------------------------------------------------------------------
# Both rendered surfaces
# ---------------------------------------------------------------------------

def test_the_cli_summary_carries_the_withdrawal_and_no_narrative_headings():
    """Surface 1: what ``nmtcapp analyze`` prints."""
    score = compute_readiness_score(_RESULT_SHAPES["low_impact"], _PASSING)
    text = score.summary()
    assert "READINESS NARRATIVE WITHDRAWN" in text, text
    for heading in ("Top Strengths:", "Areas for Improvement:"):
        assert heading not in text, (
            f"{heading!r} still renders on the CLI summary with nothing under "
            "it. An empty heading is the silent emptying T1 was written to "
            f"avoid:\n{text}"
        )


def test_the_generated_markdown_carries_the_withdrawal():
    """Surface 2: the first page of a generated application document."""
    from nmtcapp.renderers.markdown_builder import MarkdownApplicationBuilder

    app = Application(cde=CDEProfile.sample(), requested_allocation=65_000_000)
    app.add_pipeline(Pipeline.sample(n=20))
    analysis = app.analyze()
    document = MarkdownApplicationBuilder(app, analysis).build()

    summary = document[:document.index("## Table of Contents")]
    assert "READINESS NARRATIVE WITHDRAWN" in summary, summary[-2000:]
    for gone in ("**Key Strengths**",
                 "**Recommended Improvements Before Submission:**"):
        assert gone not in document, (
            f"{gone!r} still renders into the generated document."
        )
