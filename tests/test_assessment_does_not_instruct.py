"""THE ASSESSMENT SENTENCE STOPPED INSTRUCTING TOO (1.5.5 T4).

WHAT 1.5.2 DID, AND WHAT IT MISSED

1.5.2's thesis was that the composite score stops instructing: a number
built from unsourced house weights may CLASSIFY, but it may not tell a CDE
what to go and do. The withdrawal was applied to ``ReadinessScore`` --
``top_strengths``, ``top_weaknesses`` and ``recommendations`` were emptied of
composite-derived narrative -- and to the recommendation engine.

It was not applied to ``_build_peer_comparison``. Three audits scoped the
RECOMMENDATIONS. None scoped the ASSESSMENT SENTENCE, which is the line a CDE
actually reads first, on the Win Alignment Scorer, directly under the tier
badge. Through 1.5.4 it ended:

    Highly Qualified (90/100). Both sections meet the 40-point minimum.
    Priority Points: 9/10. Phase 2 review of Management Capacity and
    Capitalization Strategy will determine final ranking.
    **Focus improvement on Business Strategy (43/50).**

An INSTRUCTION, to a CDE that is already Highly Qualified, about a section
that already passes.

IT HAD NO ARITHMETIC BASIS. The aggregate is a plain sum -- 43 + 47 = 90 --
so a point in Business Strategy is worth exactly a point in Community
Outcomes. "Focus on the lower one" is a HOUSE PRIORITISATION RULE wearing the
grammar of a finding, and the tool holds no data at all on which section's
points are cheaper for a given CDE to earn. It is not a new defect; it is an
old one that five releases walked past.

THE PRINCIPLE THIS FILE ENFORCES

    A band that CLASSIFIES needs disclosure.
    A band that INSTRUCTS needs a basis.

So each branch either states a Fund-sourced fact or says nothing.

WHAT REPLACED IT, BRANCH BY BRANCH -- ALL FOUR, NOT THE ONE THAT WAS SEEN

  * HIGHLY QUALIFIED. The imperative is replaced by the fact underneath it:
    the DISTANCE of each section from the CDFI Fund's published 40-point
    section minimum. That is Fund-sourced, arithmetically checkable, and a
    disclosure rather than an instruction. It also happens to be the number a
    CDE would need in order to make the prioritisation decision ITSELF, which
    is where the decision belongs.

  * NOT QUALIFIED -- THE BRANCH A FAILING CDE READS, AND THE ONE NOBODY HAD
    LOOKED AT. It ended "Significant pipeline or CDE positioning changes are
    needed before submission." Two defects in one sentence. "Significant" is
    an unquantified magnitude judgement the tool has no basis for -- it does
    not know how large a change any given gap requires. And "before
    submission" advises against filing, which is not the tool's call: a CDE
    may submit whatever it chooses and the Fund decides. Replaced by the
    exact point shortfall to each threshold that is missed, which the branch
    was already computing and then burying under the imperative.

  * TOP TIER. Already clean -- 1.2.2 D4 removed its award prediction. Guarded
    here so it cannot regress.

  * PARTIAL. "Restore nmtc-mapper data access and re-score before drawing any
    conclusions from this partial result" SURVIVES DELIBERATELY, and this
    file asserts that it does. It is an instruction about the TOOL'S OWN
    data integrity, for which the tool has direct first-hand evidence -- it
    knows the mapper failed, because it was there. It makes no claim about
    the CDE's application and no prioritisation claim of any kind. The
    principle bars instructions without a basis, not instructions.

A LATENT DEFECT FOUND WHILE REWRITING, RECORDED SO IT IS NOT LOST

The deleted line read ``{min(bs, co)}/{BUSINESS_STRATEGY_MAX}`` -- a
HARDCODED Business Strategy denominator applied to whichever section was
lower. When Community Outcomes was the weaker one it was printed over the
Business Strategy maximum. It never rendered wrongly because both maxima are
currently 50, so the twin agreed by luck, exactly like the three copies of
``Q25_QEI_BASIS_CLAUSE``. Re-basing either section alone would have made it
visible. It is gone with the line, and
``test_no_section_total_is_printed_over_the_other_sections_maximum`` holds
the general rule.
"""
from __future__ import annotations

import re

import pytest

from nmtcapp.data.benchmark_thresholds import (
    BUSINESS_STRATEGY_MAX,
    COMMUNITY_OUTCOMES_MAX,
    HIGHLY_QUALIFIED_AGGREGATE_MIN,
    HIGHLY_QUALIFIED_SECTION_MIN,
    HOUSE_TOP_TIER_AGGREGATE_MIN,
    HOUSE_TOP_TIER_SECTION_MIN,
    PRIORITY_POINTS_MAX,
)
from nmtcapp.intelligence.win_probability import WinProbabilityScore


def _score(bs: int, co: int, tier: str, *, pp: int = 9, partial: bool = False,
           partial_note: str = "") -> WinProbabilityScore:
    return WinProbabilityScore(
        business_strategy={"section_total": bs, "max_available": BUSINESS_STRATEGY_MAX},
        community_outcomes={"section_total": co, "max_available": COMMUNITY_OUTCOMES_MAX},
        priority_points={"section_total": pp, "max_available": PRIORITY_POINTS_MAX},
        aggregate_base_score=bs + co,
        aggregate_with_priority=bs + co + pp,
        tier=tier,
        tier_gating_notes=[],
        partial=partial,
        partial_note=partial_note,
    )


#: Verbs that tell a CDE what to do with its own application. Matched
#: case-insensitively at the start of a clause, so "focus" in "the Fund's
#: focus" does not trip it but "Focus improvement on ..." does.
_IMPERATIVES = (
    "focus", "improve", "increase", "reduce", "add", "strengthen",
    "prioritise", "prioritize", "consider", "should", "must", "need to",
    "are needed", "is needed", "you should", "we recommend", "recommend",
)

#: Every branch of ``_build_peer_comparison``, including the two nobody had
#: read. Built directly rather than by scoring a pipeline, so a change in
#: sample data cannot silently stop exercising a branch.
BRANCHES = [
    ("Top Tier", _score(HOUSE_TOP_TIER_SECTION_MIN + 3, HOUSE_TOP_TIER_SECTION_MIN + 4, "Top Tier")),
    ("Highly Qualified (BS weaker)", _score(43, 47, "Highly Qualified")),
    ("Highly Qualified (CO weaker)", _score(47, 43, "Highly Qualified")),
    ("Highly Qualified (sections tied)", _score(45, 45, "Highly Qualified")),
    ("Not Qualified (both sections short)", _score(30, 32, "Not Qualified")),
    ("Not Qualified (BS short only)", _score(35, 48, "Not Qualified")),
    ("Not Qualified (CO short only)", _score(48, 35, "Not Qualified")),
    ("Not Qualified (aggregate short only)",
     _score(HIGHLY_QUALIFIED_SECTION_MIN + 1, HIGHLY_QUALIFIED_SECTION_MIN + 1, "Not Qualified")),
]


@pytest.mark.parametrize("name,score", BRANCHES, ids=[n for n, _ in BRANCHES])
def test_no_assessment_branch_instructs(name, score):
    """No branch may tell a CDE what to change about its own application."""
    text = score.peer_comparison
    hits = []
    for clause in re.split(r"[.;]\s+", text):
        stripped = clause.strip()
        low = stripped.lower()
        for verb in _IMPERATIVES:
            if low.startswith(verb) or f" {verb} " in low:
                hits.append(f"{verb!r} in {stripped!r}")
    assert not hits, (
        f"[{name}] the assessment sentence instructs. A band that classifies "
        f"needs disclosure; a band that instructs needs a basis, and the "
        f"aggregate is a plain sum so no section's points are worth more than "
        f"another's:\n  " + "\n  ".join(hits) + f"\n\nFULL TEXT:\n  {text}"
    )


@pytest.mark.parametrize("name,score", BRANCHES, ids=[n for n, _ in BRANCHES])
def test_every_branch_states_the_published_section_minimum(name, score):
    """Whatever replaces the imperative must be anchored to a Fund figure."""
    text = score.peer_comparison
    assert str(HIGHLY_QUALIFIED_SECTION_MIN) in text or \
           str(HIGHLY_QUALIFIED_AGGREGATE_MIN) in text, (
        f"[{name}] assessment names no published threshold: {text}"
    )


class TestHighlyQualified:
    def test_states_the_distance_of_each_section_from_the_minimum(self):
        score = _score(43, 47, "Highly Qualified")
        text = score.peer_comparison
        # 43 is 3 above the 40-point minimum; 47 is 7 above.
        assert "3 points above" in text, text
        assert "7 points above" in text, text
        assert "Business Strategy" in text and "Community Outcomes" in text

    def test_names_both_sections_not_only_the_weaker_one(self):
        """The 1.5.4 line named ONE section. Naming one IS the prioritisation."""
        for bs, co in [(43, 47), (47, 43), (45, 45)]:
            text = _score(bs, co, "Highly Qualified").peer_comparison
            assert text.count("Business Strategy") >= 1
            assert text.count("Community Outcomes") >= 1

    def test_arithmetic_is_correct_in_both_orders(self):
        for bs, co in [(43, 47), (47, 43), (41, 49), (50, 40)]:
            text = _score(bs, co, "Highly Qualified").peer_comparison
            assert f"{bs - HIGHLY_QUALIFIED_SECTION_MIN} point" in text, (bs, co, text)
            assert f"{co - HIGHLY_QUALIFIED_SECTION_MIN} point" in text, (bs, co, text)

    def test_a_section_exactly_on_the_minimum_reads_as_on_it(self):
        text = _score(HIGHLY_QUALIFIED_SECTION_MIN, 50, "Highly Qualified").peer_comparison
        assert ", 0 point" not in text, (
            "a section sitting ON the minimum should say so, not say '0 points above' — "
            "which is true, and reads as a rounding artefact:\n" + text
        )
        assert "exactly on it" in text, text

    def test_a_one_point_margin_is_singular(self):
        """'1 points above' is the kind of tell that makes a reader distrust the rest."""
        text = _score(HIGHLY_QUALIFIED_SECTION_MIN + 1, 50, "Highly Qualified").peer_comparison
        assert "1 point above it" in text, text
        assert "1 points" not in text, text


class TestNotQualified:
    """The branch a FAILING CDE reads — unexamined before this release."""

    def test_does_not_advise_against_submitting(self):
        text = _score(30, 32, "Not Qualified").peer_comparison
        assert "before submission" not in text.lower(), (
            "whether to file is the CDE's decision and the Fund's to judge; "
            "the tool has no standing to advise against it"
        )

    def test_makes_no_unquantified_magnitude_judgement(self):
        for bs, co in [(30, 32), (10, 12), (39, 39)]:
            text = _score(bs, co, "Not Qualified").peer_comparison
            for word in ("significant", "substantial", "major", "minor", "small"):
                assert word not in text.lower(), (
                    f"{word!r} is an unquantified magnitude judgement: {text}"
                )

    def test_states_the_exact_shortfall_to_every_missed_threshold(self):
        bs, co = 35, 32
        text = _score(bs, co, "Not Qualified").peer_comparison
        assert f"{HIGHLY_QUALIFIED_SECTION_MIN - bs} point" in text, text
        assert f"{HIGHLY_QUALIFIED_SECTION_MIN - co} point" in text, text
        agg_gap = HIGHLY_QUALIFIED_AGGREGATE_MIN - (bs + co)
        assert f"{agg_gap} point" in text, text

    def test_a_section_that_passes_is_not_listed_as_short(self):
        text = _score(48, 35, "Not Qualified").peer_comparison
        assert "Community Outcomes" in text
        short_clause = text.split("—")[-1]
        assert "Business Strategy (48" not in short_clause


class TestTopTier:
    def test_still_makes_no_award_prediction(self):
        text = _score(48, 49, "Top Tier").peer_comparison
        for banned in ("high probability", "likely to be awarded", "will be awarded"):
            assert banned not in text.lower(), text

    def test_still_says_top_tier_is_this_tools_own_label(self):
        text = _score(48, 49, "Top Tier").peer_comparison
        assert "this tool's own label" in text


class TestPartial:
    def test_the_data_integrity_instruction_survives(self):
        """DELIBERATE EXEMPTION — see this module's header.

        The tool has first-hand evidence that its own data source failed.
        Telling a reader not to rely on a degraded result is not a
        prioritisation claim about the CDE's application.
        """
        score = _score(20, 20, "Not Qualified", partial=True,
                       partial_note="eligibility source unreachable")
        text = score.peer_comparison
        assert "NOT RATED" in text
        assert "re-score" in text, (
            "the partial branch's data-integrity instruction was removed; it is "
            "exempt on purpose and its removal should be a deliberate decision"
        )


def test_no_section_total_is_printed_over_the_other_sections_maximum():
    """The general form of the latent twin the T4 rewrite removed.

    ``{min(bs, co)}/{BUSINESS_STRATEGY_MAX}`` printed whichever section was
    lower over the Business Strategy maximum. It agreed by luck because both
    maxima are 50. Re-base one and the assessment starts publishing a
    fraction whose denominator belongs to the other section.

    THIS TEST DOES NOT SKIP, and that is deliberate. The obvious shape here
    is ``pytest.skip`` when the two maxima are equal, since no rendered
    output can then reveal a mismatched denominator. But a skip is a test
    that asserts nothing, and while the maxima ARE equal — which is today,
    and every day this package has existed — the skipping version would
    assert nothing on every run, forever, while looking like coverage. It
    also cost the sdist a fiftieth skip against a stated ceiling of 49.

    THIS IS THE SOURCE-LEVEL HALF, AND IT IS A SUBSTRING CHECK. It holds one
    shape — the 1.5.4 twin, verbatim. The RENDERED half is
    ``test_the_rendered_assessment_never_prints_a_section_total_over_the_other_maximum``
    below, which holds the PROPERTY and runs unconditionally. Until the 1.5.5
    audit close, that half was guarded by
    ``if BUSINESS_STRATEGY_MAX != COMMUNITY_OUTCOMES_MAX`` and therefore
    asserted nothing on any run this package has ever had. See that test.
    """
    import inspect
    from nmtcapp.intelligence import win_probability

    # --- always: the source may not choose a total by comparison and then
    #     hand-type its denominator. This is the exact 1.5.4 shape.
    src = inspect.getsource(win_probability._build_peer_comparison)
    for line in src.splitlines():
        if line.lstrip().startswith("#"):
            continue  # comments RECORD the removed twin; that is the point
        assert "min(bs, co)" not in line and "max(bs, co)" not in line, (
            "the assessment prints a section total chosen by comparison — the "
            "1.5.4 twin printed it over a hardcoded BUSINESS_STRATEGY_MAX and "
            "agreed only because both maxima are 50:\n" + line
        )

    # The rendered half is no longer here. It was
    #
    #     if BUSINESS_STRATEGY_MAX != COMMUNITY_OUTCOMES_MAX:
    #         ...
    #
    # and that condition is FALSE — today, and on every run this package has
    # ever had, because both maxima are 50 and always have been. Three
    # indented assertions that never executed. It is parametrised instead, in
    # the test below.


#: Maxima to re-base one section to, so the two stop agreeing and a
#: mismatched denominator becomes VISIBLE in the rendered text.
#:
#: Both directions, because a gate that only ever raises one maximum tests
#: one substitution. Values are deliberately not multiples of each other and
#: not equal to any section total used below, so a forbidden string cannot
#: coincide with a legitimate one by arithmetic accident.
_REBASED_MAXIMA = [("COMMUNITY_OUTCOMES_MAX", 40), ("BUSINESS_STRATEGY_MAX", 63)]

#: (bs, co, tier) triples where the branch prints BOTH section totals, so
#: both directions of the swap are observable. ``bs != co`` in every one: at
#: bs == co the correct string and the swapped string are the same characters
#: and the gate could not tell them apart.
_BOTH_SECTIONS_PRINTED = [
    (43, 47, "Highly Qualified"),
    (47, 43, "Highly Qualified"),
    (35, 32, "Not Qualified"),
    (32, 35, "Not Qualified"),
]


@pytest.mark.parametrize("attr, rebased", _REBASED_MAXIMA)
@pytest.mark.parametrize("bs, co, tier", _BOTH_SECTIONS_PRINTED)
def test_the_rendered_assessment_never_prints_a_section_total_over_the_other_maximum(
    monkeypatch, attr, rebased, bs, co, tier
):
    """THE PROPERTY, NOT THE SUBSTRING (1.5.5 audit B3).

    THE DEFECT THIS CLOSES. This assertion used to live inside
    ``if BUSINESS_STRATEGY_MAX != COMMUNITY_OUTCOMES_MAX``. Both maxima are
    50, so the condition has been false on every run since the package
    existed, and the rendered half of the twin gate asserted NOTHING while
    reading like coverage.

    Measured, not argued. Print Community Outcomes over
    ``BUSINESS_STRATEGY_MAX`` — the audit's mutation (b) — and the rendered
    text is BYTE-IDENTICAL, sha256 unchanged across all three branches,
    because the two denominators are the same number. The full suite ran
    green: not this gate, not the attribution sweep, not the pinned
    constants, not the threshold twins. 1,561 passed.

    THE FIX IS TO STOP DEPENDING ON THE ACCIDENT. One maximum is re-based at
    runtime so the two disagree, and the rendered text is then read for a
    section total printed over the OTHER section's denominator. The check
    runs on every run, in both directions, on four score shapes.

    ``_build_peer_comparison`` reads both maxima as module globals inside its
    body, so ``monkeypatch.setattr`` on the module reaches them. That is a
    property of the code under test and is asserted below rather than
    assumed: if the function is ever changed to close over the values at
    import time, the re-base stops taking effect and this gate would go
    quietly green again — so it checks that the denominator actually moved.
    """
    from nmtcapp.intelligence import win_probability

    monkeypatch.setattr(win_probability, attr, rebased)
    bs_max = win_probability.BUSINESS_STRATEGY_MAX
    co_max = win_probability.COMMUNITY_OUTCOMES_MAX
    assert bs_max != co_max, "the re-base did not take; the gate is vacuous"
    assert bs != co, "at bs == co the swapped string is the correct one"

    text = _score(bs, co, tier).peer_comparison

    # PROOF OF LIFE. If the re-base did not reach the rendered text at all —
    # a global captured at import, a cached string, a refactor to a constant
    # — every "not in" below would pass over text that never moved.
    assert f"{bs}/{bs_max}" in text and f"{co}/{co_max}" in text, (
        f"re-basing {attr} to {rebased} did not reach the rendered "
        f"assessment. Expected '{bs}/{bs_max}' and '{co}/{co_max}' in:\n{text}"
    )

    assert f"{bs}/{co_max}" not in text, (
        f"Business Strategy's total is printed over Community Outcomes' "
        f"maximum ('{bs}/{co_max}'). The two agree at 50 in the shipped "
        f"configuration, so this renders identically today and is invisible "
        f"without re-basing:\n{text}"
    )
    assert f"{co}/{bs_max}" not in text, (
        f"Community Outcomes' total is printed over Business Strategy's "
        f"maximum ('{co}/{bs_max}') — the audit's mutation (b), which is "
        f"byte-identical in the shipped configuration:\n{text}"
    )
