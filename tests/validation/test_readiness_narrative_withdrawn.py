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

THE COVERAGE PROBLEM THIS MODULE EXISTS TO SOLVE — AND THE FALSE DIAGNOSIS THAT
SHIPPED WITH IT IN 1.5.2, CORRECTED HERE

1.5.1's F2 finding was that both shipped readiness fixtures score geographic
diversity above 70, so two withdrawn branches were never entered by any test.
1.5.2 measured a real gap one level deeper — restoring ``_identify_strengths``'s
eligibility branch turned SEVEN of this module's cases red and left every
``pipeline:`` case green — and then attributed it to the wrong cause. What this
docstring said, in block capitals, was:

    ``nmtc_mapper`` IS NOT INSTALLED IN THIS SUITE'S ENVIRONMENT.

ALL THREE LIMBS OF THAT WERE FALSE, and the audit that found it is the reason
this paragraph exists. Re-derived by execution, not by reading:

1. THE LIBRARY IS INSTALLED. The DISTRIBUTION is ``nmtc-mapper`` (0.5.0, the
   floor ``pyproject.toml`` pins); the IMPORT NAME is ``nmtcmapper``. The round
   probed ``import nmtc_mapper``, which raises, and read the raise as absence.
   This package's own contract gate has always known the right name —
   ``tests/integrations/test_mapper_contract.py`` imports
   ``nmtcmapper.eligibility.checker`` and passes.
2. THE LIVE PATH RUNS. ``NMTCMapper()`` loads 85,395 census tracts from the
   cached CDFI Fund workbook, reports ``data_source == "cdfi_fund"``, geocodes,
   and ``enrich_pipeline_eligibility`` returns
   ``eligibility_data_status == "ok"``.
3. THE SUITE REACHES SIX COMPONENTS CONSTANTLY. Instrumenting every
   ``compute_readiness_score`` call across the suite: 429 calls, 339 of them
   six-component, 165 of those reached through ``Application.analyze()``, from
   147 distinct tests in 31 files. Six of those tests reach six components
   through the adapter's REAL live path — ``_enrich_via_api`` with an actual
   ``NMTCMapper``, not a mock.

WHY A TRUE MEASUREMENT PRODUCED A FALSE DIAGNOSIS, WHICH IS THE LESSON WORTH
KEEPING. The seven-red row above reproduces exactly. Its cause is not the
environment: it is THIS FILE. ``_project`` sets ``is_nmtc_eligible=True``, so
every fixture project is already ``is_enriched``; the adapter short-circuits on
"all projects already enriched", declines to vouch for a provenance the run
cannot support, and stamps ``pre_enriched`` over ``Pipeline.__init__``'s
fail-closed ``"unenriched"``. THE FIXTURES ARE DEGRADED BECAUSE THIS MODULE
BUILDS THEM DEGRADED. Deleting the library would not change the measurement by
one case, and installing it does not change it either.

The mechanism that carries the rest of the suite to six is ``Pipeline.sample()``
(``nmtcapp/core/pipeline.py``), the one construction path documented as allowed
to vouch for its own pre-verified eligibility data. The round never looked
there.

So this module drives THREE fixture shapes deliberately:

* ``pipeline:``  — pipelines through ``Application.analyze()`` left in the
  degraded four. Two tests below assert that degraded path on purpose, so it
  stays.
* ``enriched:``  — a pipeline through ``Application.analyze()`` stamped ``"ok"``
  the way ``Pipeline.sample()`` stamps itself, reaching the full six. This is
  the shape 1.5.2 lacked, and it is what makes the pipeline path sensitive to
  an eligibility or distress reversion at all. Measured: with it present, the
  same eligibility reversion that produced seven red now produces eight, and
  the eighth is a ``pipeline`` case.
* ``result:``    — hand-built ``PipelineAnalysisResult`` objects, the same
  construction ``conftest``'s ``sample_pipeline_result`` uses, spanning both
  ends of every band.

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


def _score_from_pipeline(spec, *, enriched: bool = False):
    """Score a pipeline built by hand and run through ``Application.analyze()``.

    ``enriched=False`` (the default) leaves the pipeline DEGRADED, and the cause
    is this function, not the environment. ``_project`` populates
    ``is_nmtc_eligible``, so the adapter takes its "already enriched"
    short-circuit, performs no CDFI Fund lookup, and stamps ``pre_enriched`` —
    correctly, since nothing here was tool-verified. Four components result.

    ``enriched=True`` stamps ``"ok"`` before ``analyze()``, which is exactly
    what ``Pipeline.sample()`` does at construction and for the same stated
    reason: a fixture that ships pre-verified eligibility data is the one
    construction allowed to vouch for it. Six components result. This is a
    FIXTURE claim about a FIXTURE, not a provenance claim about live data — no
    production path may set this attribute itself.
    """
    projects = [_project(i, *args) for i, args in enumerate(spec)]
    app = Application(
        cde=CDEProfile.sample(),
        requested_allocation=sum(p.qei_request for p in projects),
    )
    pipeline = Pipeline(projects=projects)
    if enriched:
        pipeline.eligibility_data_status = "ok"
    app.add_pipeline(pipeline)
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

#: THE SHAPE 1.5.2 LACKED, and the reason it lacked it was a false belief about
#: the environment rather than a judgement about coverage. Same construction as
#: above, same ``Application.analyze()`` call, one attribute different — and
#: with it the pipeline path reaches all SIX components and becomes sensitive to
#: a reversion in ``_eligibility_score`` or ``_distress_score``.
#:
#: Sized on purpose so one shape enters three withdrawn branches at once, each
#: verified by ``test_the_enriched_pipeline_shape_reaches_six_components``:
#:     eligibility_quality  100.0  >= 80  — _identify_strengths' eligibility arm
#:     distress_concentration 0.0  <  75  — _build_recommendations' distress arm
#:     impact_metrics        13.5  <  60  — _build_recommendations' impact arm
_ENRICHED_PIPELINE_SHAPES = {
    "lic_only_low_impact": [(s, 10_000_000, "lic", 25) for s in
                            ("IL", "OH", "MI", "IN")],
}


# ---------------------------------------------------------------------------
# Fixtures — path B: hand-built results (full six components)
# ---------------------------------------------------------------------------

def _result(eligibility_pct, pct_deep_or_severe, states, hhi, jobs_per_mm):
    """A PipelineAnalysisResult with eligibility data PRESENT.

    Built directly rather than through Application.analyze() so that the two
    eligibility-dependent components can be DIALLED to either side of every
    band independently of what a real pipeline of PipelineProjects happens to
    produce — ``_project`` fixes ``is_nmtc_eligible=True``, so an analysed
    pipeline can only ever land eligibility_quality at 100.

    NOT because the library is missing. 1.5.2 said that here and it was false:
    ``nmtcmapper`` 0.5.0 is installed and the live path runs. See the module
    docstring. ``_ENRICHED_PIPELINE_SHAPES`` now covers the analysed route to
    six components; these hand-built results cover the range.
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

def test_the_library_this_module_once_declared_missing_is_installed():
    """B1. The correction, asserted rather than narrated.

    1.5.2 shipped ``nmtc_mapper IS NOT INSTALLED IN THIS SUITE'S ENVIRONMENT``
    in this docstring and in the CHANGELOG. It was false three ways, and the
    first way is why the other two followed: the round probed the DISTRIBUTION
    name with an underscore. The import name has no underscore.

    Both spellings are asserted, in both directions, so the sentence cannot
    come back. If ``nmtc_mapper`` ever becomes importable this fails and the
    correction gets re-read rather than silently rotting.
    """
    import importlib

    importlib.import_module("nmtcmapper")

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("nmtc_mapper")

    from importlib.metadata import version
    assert version("nmtc-mapper") >= "0.5.0", (
        "the distribution is installed under the name nmtc-mapper; only the "
        "import name is nmtcmapper. Neither is absent."
    )


def test_the_degraded_pipeline_fixtures_are_degraded_by_construction():
    """FAIL CLOSED on the CORRECTED diagnosis, which is a fact about this file.

    The three ``_PIPELINE_SHAPES`` are degraded because ``_project`` populates
    ``is_nmtc_eligible``, so the adapter short-circuits on "already enriched"
    and stamps ``pre_enriched`` rather than performing a lookup it did not
    perform. The library's presence is irrelevant to this, and
    ``test_the_library_this_module_once_declared_missing_is_installed`` above
    pins that it IS present.

    The status is asserted by name, not merely as "not ok": ``pre_enriched``
    and ``unavailable`` are different findings and only one of them is a fact
    about this fixture.
    """
    from nmtcapp.core.application import Application as _App

    projects = [_project(i, *args) for i, args in
                enumerate(_PIPELINE_SHAPES["middling"])]
    assert all(p.is_enriched for p in projects), (
        "the short-circuit this test is about is keyed on is_enriched"
    )
    app = _App(cde=CDEProfile.sample(), requested_allocation=30_000_000)
    app.add_pipeline(Pipeline(projects=projects))
    analysis = app.analyze()
    assert analysis.pipeline_result.eligibility_data_status == "pre_enriched", (
        "the fixture is no longer degraded by the caller-supplied-eligibility "
        "route. Re-read this module's premise before adjusting the assertion: "
        "the 1.5.2 version of this test blamed a missing library for this and "
        f"was wrong. Status: {analysis.pipeline_result.eligibility_data_status}"
    )

    score = _score_from_pipeline(_PIPELINE_SHAPES["middling"])
    assert score.partial
    assert set(score.component_scores) == {
        "geographic_diversity", "impact_metrics",
        "validation_pass_rate", "completeness",
    }, score.component_scores


def test_the_enriched_pipeline_shape_reaches_six_components():
    """FAIL CLOSED for the shape 1.5.2 lacked.

    One attribute separates this from the test above. If it stops reaching six
    components — or stops landing on the three bands it was sized for — every
    ``enriched:`` case below goes quietly vacuous and the pipeline path loses
    its only sensitivity to an eligibility or distress reversion.
    """
    score = _score_from_pipeline(
        _ENRICHED_PIPELINE_SHAPES["lic_only_low_impact"], enriched=True
    )
    assert not score.partial, score.partial_note
    assert set(score.component_scores) == {
        "eligibility_quality", "distress_concentration",
        "geographic_diversity", "impact_metrics",
        "validation_pass_rate", "completeness",
    }, score.component_scores

    # The three withdrawn branches this one shape is sized to enter, read off
    # the same cuts the hand-built fixtures use.
    c = score.component_scores
    assert c["eligibility_quality"] >= 80, c    # _identify_strengths
    assert c["distress_concentration"] < 75, c  # _build_recommendations
    assert c["impact_metrics"] < 60, c          # _build_recommendations


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
    for label, spec in _ENRICHED_PIPELINE_SHAPES.items():
        yield f"enriched:{label}", _score_from_pipeline(spec, enriched=True)
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

    Two emitters in ``_build_recommendations`` are deliberately retained — the
    degraded-data notice and the validation-issue echo — because NO HOUSE BAND
    DECIDES WHETHER EITHER FIRES. This asserts that what survives is EXACTLY
    those two, so a future edit cannot smuggle a band-triggered line back in
    under the heading that says these are not composite-derived.

    NOT "neither reads ``component_scores``", which is what 1.5.2 wrote here
    and in the function's own docstring, and which is false of the first one
    (1.5.2 audit, F6): the degraded-data notice triggers on
    ``"distress_concentration" not in scores`` — a membership test on
    ``component_scores``. It reads the KEY SET, never a value, and key absence
    is a fact about the run rather than a band that was crossed. The code was
    right; the reason given for it was not.
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
    """The other retained emitter, on the path that produces it.

    And its mirror: the notice must NOT fire on the enriched shape, or it is
    not a fact about the run at all.
    """
    score = _score_from_pipeline(_PIPELINE_SHAPES["middling"])
    assert any(r.startswith("Restore eligibility data access")
               for r in score.recommendations), score.recommendations

    ok = _score_from_pipeline(
        _ENRICHED_PIPELINE_SHAPES["lic_only_low_impact"], enriched=True
    )
    assert not any(r.startswith("Restore eligibility data access")
                   for r in ok.recommendations), ok.recommendations


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
        # WHITESPACE-NORMALISED (1.5.3 follow-up). The deduction column is
        # padded to a fixed width so the row head is a constant 78 columns,
        # which renders "DOCKED  5.0 POINTS" for a one-digit deduction. The
        # claim being asserted is that the note STATES the deduction, not how
        # many spaces precede it, so the comparison collapses runs of
        # whitespace on both sides. The number and the words are still
        # required, still adjacent, still in order.
        assert f"DOCKED {dock:.1f} POINTS" in " ".join(note.split()), (
            f"{label}: the note does not state {pretty}'s deduction of "
            f"{dock:.1f} points:\n{note}"
        )
    assert f"TOTAL DEDUCTION {total:.1f} POINTS" in " ".join(note.split()), (
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
