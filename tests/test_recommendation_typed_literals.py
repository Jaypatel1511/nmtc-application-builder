"""TWO DISPLAY LITERALS BESIDE THE CONSTANTS THEY SHOULD READ (1.5.4 T7).

Both are the class ``intelligence/recommendations``' own module header forbids
at lines 43-63 — "a display literal beside a comparison that reads the
constant, so the printed explanation and the applied rule are joined by nothing
but a coincidence of typing".

  recommendations.py:959   quantified_improvement="Reaching 98% eligibility
                           significantly improves Pipeline Credibility."
                           The literal ``98%`` sits beside an ``action`` that
                           interpolates ``_ELIGIBLE_STRONG_TEXT``. Move
                           WINNER_PATTERN_THRESHOLDS["min_eligible_pct"]
                           ["strong"] and the two sentences disagree — inside
                           one recommendation.

  recommendations.py:1026  f"Not Qualified ({agg}/100) — {gap_str}." types
                           ``/100`` while every sibling branch (Top Tier,
                           Highly Qualified, and ``gap_str``'s own aggregate
                           clause three lines above) uses ``_AGGREGATE_MAX``.
                           And it is in the branch a FAILING CDE reads.

NEITHER IS A WRONG NUMBER TODAY. ``strong`` is 0.98 and
BUSINESS_STRATEGY_MAX + COMMUNITY_OUTCOMES_MAX is 100, so both literals match.
THAT IS EXACTLY WHY THEY NEED FIXING: the 1.5.1 audit's instance 25 was four
percentiles that had agreed by luck and the entire suite stayed green. A gate
that asserts the current value would stay green too — so the gates below MOVE
THE CONSTANT and assert the rendered sentence follows it.
"""
from __future__ import annotations

import re

import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline
from nmtcapp.intelligence import recommendations as rec_mod
from nmtcapp.intelligence.recommendations import RecommendationEngine


def _fallback_recs(pipeline_result):
    """The no-score path, which is where the 98% literal lives."""
    return RecommendationEngine().recommend(pipeline_result, None, None)


@pytest.fixture
def low_eligibility_result():
    pipeline = Pipeline.sample(n=10)
    for project in pipeline:
        project.is_nmtc_eligible = False
        project.distress_level = "ineligible"
    app = Application(cde=CDEProfile.sample(), requested_allocation=65_000_000)
    app.add_pipeline(pipeline)
    return app.analyze().pipeline_result


def test_the_eligibility_target_follows_its_constant(
    monkeypatch, low_eligibility_result
):
    """Move the band; the estimate must move with it."""
    monkeypatch.setattr(rec_mod, "_ELIGIBLE_STRONG_TEXT", "77%")
    recs = _fallback_recs(low_eligibility_result)
    matching = [
        r for r in recs.recommendations
        if "eligibility rate" in r.finding
    ]
    assert matching, "precondition: the eligibility fallback item did not fire"
    text = " ".join(matching[0].quantified_improvement.split())
    assert "77%" in text, (
        "the estimate does not read _ELIGIBLE_STRONG_TEXT — it types its own "
        f"percentage beside an action that interpolates the constant:\n{text}"
    )
    assert "98%" not in text, (
        f"a typed 98% survives in the estimate after the band moved:\n{text}"
    )


def test_the_eligibility_action_and_estimate_name_the_same_band(
    low_eligibility_result
):
    """The two sentences are in ONE recommendation and must agree."""
    recs = _fallback_recs(low_eligibility_result)
    matching = [r for r in recs.recommendations if "eligibility rate" in r.finding]
    assert matching, "precondition"
    item = matching[0]
    band = rec_mod._ELIGIBLE_STRONG_TEXT
    assert band in item.action and band in item.quantified_improvement, (
        f"action and estimate disagree about the target band ({band}):\n"
        f"  action:   {item.action}\n  estimate: {item.quantified_improvement}"
    )


def test_the_not_qualified_denominator_follows_the_section_maxima(monkeypatch):
    """``/100`` was typed in the branch a failing CDE reads."""
    monkeypatch.setattr(rec_mod, "_AGGREGATE_MAX", 90)
    engine = RecommendationEngine()

    class _Score:
        tier = "Not Qualified"
        aggregate_base_score = 41
        business_strategy = {"section_total": 20}
        community_outcomes = {"section_total": 21}
        partial = False
        unsupplied_inputs: dict = {}

    assessment = engine._overall_assessment(_Score(), None)
    assert "/90" in assessment, (
        "the Not Qualified verdict types its own denominator instead of "
        f"reading _AGGREGATE_MAX:\n{assessment}"
    )
    assert "/100" not in assessment, (
        f"a typed /100 survives after the section maxima moved:\n{assessment}"
    )


@pytest.mark.parametrize("tier,agg,bs,co", [
    ("Top Tier", 96, 46, 50),
    ("Highly Qualified", 88, 44, 44),
    ("Not Qualified", 41, 20, 21),
])
def test_every_tier_verdict_uses_the_same_denominator(monkeypatch, tier, agg, bs, co):
    """Three branches, one denominator. The odd one out was the failing branch."""
    monkeypatch.setattr(rec_mod, "_AGGREGATE_MAX", 90)

    class _Score:
        partial = False
        unsupplied_inputs: dict = {}

    score = _Score()
    score.tier = tier
    score.aggregate_base_score = agg
    score.business_strategy = {"section_total": bs}
    score.community_outcomes = {"section_total": co}

    assessment = RecommendationEngine()._overall_assessment(score, None)
    assert f"{agg}/90" in assessment, (
        f"the {tier} verdict does not render the aggregate over "
        f"_AGGREGATE_MAX:\n{assessment}"
    )


def test_no_recommendation_string_types_a_bare_hundred_denominator():
    """The class, swept over the module's own source.

    ``/100`` beside an aggregate is the shape; ``_AGGREGATE_MAX`` is the fix.
    Scoped to the aggregate because ``/100`` is a legitimate literal elsewhere
    (a readiness headline is genuinely out of a typed 100).
    """
    import inspect
    source = inspect.getsource(rec_mod)
    offenders = [
        line.strip()
        for line in source.split("\n")
        if re.search(r"\{agg[a-z_]*\}\s*/\s*100", line)
    ]
    assert not offenders, (
        "an aggregate is rendered over a typed 100 rather than over "
        f"_AGGREGATE_MAX:\n  " + "\n  ".join(offenders)
    )
