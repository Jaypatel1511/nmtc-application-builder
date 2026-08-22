"""F2 (1.5.1 audit) — the five 1.5.1 fixes that nothing asserted.

THE FINDING. The audit re-added ``"Expand geographic footprint… Target ≥5
states"``, restored ``"Application not viable in current form"``, and dropped
the T5 strength guard — and **each of those reversions passed all 1,244
tests**. A round whose entire subject was disclosure shipped disclosures that
no test rendered.

THE ROOT CAUSE, and it is one line. Both readiness fixtures score geographic
diversity above 70:

    Pipeline.sample(n=20)   19 states, HHI 592   -> 100.0
    Pipeline.sample(n=5)     5 states, HHI 2109  -> 100.0

``_build_recommendations``'s geographic branch and ``_identify_weaknesses``'s
geographic branch are both BELOW those numbers, so neither branch was ever
entered by any test in the suite. The withdrawal notice — the string that tells
a CDE the advice it acted on last week has been retracted — was rendered by
nothing at all.

WHAT THIS MODULE DOES. It builds pipelines that are deliberately concentrated,
so every branch of ``_geo_score``'s consumers is exercised, and then asserts the
five fixes:

    1. the withdrawal notice, and that no surface instructs adding states
    2. the docs text (B2's page and its four sweep siblings)
    3. the T5 strength guard
    4. the Streamlit rendering (F1)
    5. B2's published page

Each is proved red by reversion in the round's report. Where a fix could not be
gated, this module says so in the test's own docstring rather than leaving the
gap silent.
"""
from __future__ import annotations

import io
import os
import re

import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline, PipelineProject
from nmtcapp.data.schema import (
    MIN_GEOGRAPHIC_DIVERSITY,
    READINESS_SCORING_WEIGHTS,
)
from nmtcapp.validation.readiness_score import compute_readiness_score

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Fixtures that actually reach the branches
# ---------------------------------------------------------------------------

def _pipeline(state_qei):
    """A pipeline whose QEI is distributed exactly as given.

    Concentration is the point: the shipped fixtures are diverse, which is why
    every geographic branch below 70 went unexercised for twenty-three
    releases.
    """
    projects = []
    for index, (state, qei) in enumerate(state_qei):
        projects.append(PipelineProject(
            project_id=f"GEO-{index:03d}",
            project_name=f"Geo Fixture {index}",
            qalicb_name=f"Geo QALICB {index} LLC",
            address=f"{index} Fixture St",
            city="Fixture City",
            state=state,
            sector="healthcare",
            project_type="operating_business",
            total_project_cost=int(qei * 1.4),
            qei_request=qei,
            qlici_amount=qei,
            expected_jobs_created=200,
            expected_jobs_retained=50,
            census_tract="17031010100",
            is_nmtc_eligible=True,
            distress_level="severe",
            is_native_area=False,
            is_high_migration_rural=False,
            is_opportunity_zone=False,
        ))
    app = Application(
        cde=CDEProfile.sample(),
        requested_allocation=sum(q for _, q in state_qei),
    )
    app.add_pipeline(Pipeline(projects=projects))
    return app


#: (label, spec, expected geographic sub-score band). The bands are what make
#: this module a coverage claim rather than four arbitrary pipelines.
_SHAPES = {
    "one_state":        [("IL", 20_000_000), ("IL", 20_000_000)],
    "two_states":       [("IL", 38_000_000), ("OH", 2_000_000)],
    "three_states":     [("IL", 36_000_000), ("OH", 2_000_000), ("MI", 2_000_000)],
    "four_states":      [("IL", 30_000_000), ("OH", 4_000_000),
                         ("MI", 3_000_000), ("IN", 3_000_000)],
    "six_states_conc":  [("IL", 39_000_000)] + [
                         (s, 200_000) for s in ("OH", "MI", "IN", "WI", "MN")],
}


def _readiness(spec):
    app = _pipeline(spec)
    analysis = app.analyze()
    return compute_readiness_score(
        analysis.pipeline_result, analysis.validation_results
    ), analysis


def _all_emitted(score) -> list:
    return list(score.top_strengths) + list(score.top_weaknesses) + list(score.recommendations)


# ---------------------------------------------------------------------------
# The coverage claim itself
# ---------------------------------------------------------------------------

def test_these_fixtures_actually_reach_the_branches_the_shipped_ones_missed():
    """FAIL CLOSED. If these pipelines stop being concentrated, everything
    below goes quietly vacuous — which is precisely how the 1.5.1 round shipped
    five ungated fixes.

    Asserts the sub-score bands, not just that the fixtures exist.
    """
    bands = {}
    for label, spec in _SHAPES.items():
        score, _ = _readiness(spec)
        bands[label] = score.component_scores["geographic_diversity"]

    assert bands["one_state"] < 50, bands
    assert bands["two_states"] < 50, bands
    assert 50 <= bands["three_states"] < 60, bands
    assert 60 <= bands["four_states"] < 100, bands
    assert bands["six_states_conc"] >= 70, bands

    # And the shipped fixtures must still be the diverse ones, so the contrast
    # this module exists for is real.
    for n in (5, 20):
        app = Application(cde=CDEProfile.sample(), requested_allocation=65_000_000)
        app.add_pipeline(Pipeline.sample(n=n))
        analysis = app.analyze()
        shipped = compute_readiness_score(
            analysis.pipeline_result, analysis.validation_results
        ).component_scores["geographic_diversity"]
        assert shipped >= 70, (
            f"Pipeline.sample(n={n}) now scores {shipped} on geographic "
            "diversity. If it has dropped below 70 the branches below are "
            "reachable from the shipped fixtures too, and this module's "
            "premise needs re-reading — not deleting."
        )


# ---------------------------------------------------------------------------
# FIX 1 — the withdrawal notice, and the instruction that must not return
# ---------------------------------------------------------------------------

#: Every phrasing of the advice T1 withdrew. Reverting the fix re-introduces
#: one of these, and this is the assertion that goes red when it does.
_WITHDRAWN_INSTRUCTIONS = (
    "expand geographic footprint",
    "target ≥5 states",
    "target >=5 states",
    "add more states",
    "too narrow",
    "application not viable in current form",
)


@pytest.mark.parametrize("label", sorted(_SHAPES))
def test_no_surface_instructs_the_cde_to_add_states(label):
    """FIX 1, and the class behind it.

    T1 withdrew the recommendation AND the weakness string. This asserts the
    property rather than either site: across strengths, weaknesses and
    recommendations, on pipelines from one state to six, nothing tells a CDE to
    add states and nothing calls a footprint too narrow.

    Re-adding "Expand geographic footprint — currently N states. Target ≥5
    states" to _build_recommendations turns this red on four of the five
    shapes. Before this module it turned nothing red.
    """
    score, _ = _readiness(_SHAPES[label])
    emitted = " || ".join(_all_emitted(score)).lower()
    offenders = [p for p in _WITHDRAWN_INSTRUCTIONS if p in emitted]
    assert not offenders, (
        f"{label}: the readiness engine emitted withdrawn instruction(s) "
        f"{offenders}.\n\nThe CY 2024-2025 Review Process scores no state "
        "count, and expanding a footprint to raise this tool's own "
        "geographic sub-score can dilute deep/severe distress, which the Fund "
        f"does score.\n\nEmitted:\n" + "\n".join(f"  - {s}" for s in _all_emitted(score))
    )


@pytest.mark.parametrize("label", ["one_state", "two_states", "three_states", "four_states"])
def test_a_pipeline_docked_on_geography_is_told_that_it_was(label):
    """FIX 1 + F4's second half. Silence plus a deduction is worse than either.

    THE FOUR-STATE CASE IS THE ONE THAT MATTERS. It scores 66.7, which cleared
    the old ``< 60`` notice AND the ``< 50`` weakness, so it was docked 4.99
    points of the headline it is shown and told nothing anywhere. The trigger
    is now "this component cost you points".
    """
    score, _ = _readiness(_SHAPES[label])
    sub = score.component_scores["geographic_diversity"]
    assert sub < 100, f"{label} is not docked; this case belongs elsewhere"

    # RE-POINTED IN 1.5.2, PROPERTY UNCHANGED. Through 1.5.1 the notice was
    # one entry in ``recommendations``. T1 withdrew that whole list, so the
    # notice moved to ``narrative_note`` — but F4's rule ("a tool may decline
    # to advise; it may not deduct silently") did not move, and it now binds
    # on all six components rather than on geography alone. This test keeps
    # asserting geography's share of it.
    assert score.narrative_withdrawn, (
        f"{label}: narrative_withdrawn is False. A consumer reading to_dict() "
        "cannot tell a withdrawn narrative from an empty one."
    )
    text = score.narrative_note
    assert "WITHDRAWN" in text, (
        f"{label}: geographic sub-score is {sub} — a deduction of "
        f"{(100 - sub) * READINESS_SCORING_WEIGHTS['geographic_diversity']:.2f} "
        "points — and no withdrawal notice was emitted at all.\n\n"
        "A tool may decline to advise. It may not deduct silently.\n\n"
        f"narrative_note:\n{text}"
    )

    expected_dock = (100.0 - sub) * READINESS_SCORING_WEIGHTS["geographic_diversity"]
    # Whitespace-normalised: the deduction column is padded to a fixed width
    # (1.5.3), so a one-digit deduction renders "DOCKED  5.0 POINTS". What is
    # asserted is that the deduction is STATED, not its column padding.
    assert f"DOCKED {expected_dock:.1f} POINTS" in " ".join(text.split()), (
        f"{label}: the notice does not state the deduction it should "
        f"({expected_dock:.1f} points). Text:\n{text}"
    )

    # THE PERCENTAGE IS DERIVED, NOT TYPED BESIDE THE COMPARISON. This is the
    # display-literal rule the recommendations module's header states: a
    # printed figure and the applied weight must be the same object.
    weight = READINESS_SCORING_WEIGHTS["geographic_diversity"]
    assert f"{weight:.0%} weight" in text, (
        f"{label}: the notice's weight figure is not derived from "
        f"READINESS_SCORING_WEIGHTS['geographic_diversity'] ({weight:.0%}). "
        f"Text:\n{text}"
    )

    # And it must say the deduction is not a finding about the application.
    for required in ("does not score geographic breadth",
                     "footprint as a finding either way"):
        assert required in text, f"{label}: notice omits {required!r}:\n{text}"

    # 1.5.2: the deduction line must NAME the component, because the note now
    # accounts for six of them and an unlabelled figure would be unreadable.
    assert "Geographic Diversity" in text, (
        f"{label}: the deduction table does not name the geographic "
        f"component:\n{text}"
    )


def test_the_withdrawal_notice_names_what_was_withdrawn():
    """FIX 1. A withdrawn recommendation and an absent one read differently.

    T1's stated reason for a notice rather than a deletion was that a CDE who
    ran the tool last week needs to know the advice was retracted. That is only
    true if the notice says what the advice WAS.
    """
    score, _ = _readiness(_SHAPES["one_state"])
    notice = score.narrative_note
    assert "WITHDRAWN" in notice, notice
    # 1.5.2 widened this from the geographic advice to the whole narrative, so
    # the notice must now name what ALL THREE lists used to say. ">=5 states"
    # replaces "≥5 states": the note is rendered into a fixed-width CLI block
    # and into markdown, and the 1.5.1 string was the only non-ASCII token in
    # either.
    for required in ("Earlier versions", ">=5 states",
                     "strengths", "weaknesses", "recommendations"):
        assert required in notice, f"notice omits {required!r}:\n{notice}"


# ---------------------------------------------------------------------------
# FIX 3 — the T5 strength guard
# ---------------------------------------------------------------------------

def test_the_diversity_strength_is_not_claimed_over_a_concentrated_pipeline():
    """FIX 3 (T5). The contradiction, on the fixture that produces it.

    ``_geo_score``'s first term reaches 100 at ``MIN_GEOGRAPHIC_DIVERSITY * 2``
    states, so from five states up the state count alone clears the 70 gate and
    the HHI term is inert. The six-state fixture holds ~97.5% of QEI in one
    state — printed ``highly_concentrated`` by geographic_analysis one block
    above — and scored 100.0.

    Dropping the ``not _concentrated`` guard turns this red. Before this module
    it turned nothing red.

    VACUOUS SINCE 1.5.2 T1, AND SAID SO HERE RATHER THAN LEFT SILENT. T1
    withdrew every strength, so ``top_strengths`` is empty on every pipeline
    and this assertion can no longer fail by way of the guard it was written
    for. It is retained because the band assertion above it still proves the
    fixture reaches the contradiction window, which is what a 2.0.0
    re-introduction would have to get past — but a green here is now evidence
    of the withdrawal, NOT evidence that the T5 guard still works.
    """
    score, analysis = _readiness(_SHAPES["six_states_conc"])
    geo = analysis.pipeline_result.geographic_diversity

    assert geo["geographic_concentration_label"] == "highly_concentrated", geo
    assert score.component_scores["geographic_diversity"] >= 70, (
        "the fixture no longer reaches the strength gate, so this test would "
        "pass vacuously"
    )

    diversity_claims = [
        s for s in score.top_strengths if "geographic" in s.lower()
    ]
    assert not diversity_claims, (
        "the readiness score asserted a geographic-diversity STRENGTH over a "
        "pipeline its own concentration measure calls 'highly_concentrated', "
        f"in the same document:\n  {diversity_claims}\n\n"
        f"HHI = {geo['hhi']:.0f}, states = {geo['states_count']}, sub-score = "
        f"{score.component_scores['geographic_diversity']}"
    )


def test_the_contradiction_window_opens_at_five_states_not_six():
    """The window is wider than the round believed, and it is derived here.

    The 1.5.1 entry records this: the strength gate is >=70 and the state term
    alone reaches 83.3 at five states. Derived from the constant rather than
    restated, so re-basing MIN_GEOGRAPHIC_DIVERSITY moves the claim with it.
    """
    def state_term(n):
        return min(100.0, n / MIN_GEOGRAPHIC_DIVERSITY * 50.0)

    assert state_term(5) >= 70, state_term(5)
    assert state_term(4) < 70, state_term(4)


def test_the_geographic_strength_no_longer_exists_to_carry_a_basis():
    """SUPERSEDED BY 1.5.2 T1, AND REWRITTEN RATHER THAN DELETED.

    WHAT THIS TEST USED TO ASSERT. F4's first half: the geographic WEAKNESS
    carried "this tool's own house curve — not a CDFI Fund threshold" and the
    STRENGTH did not, and uncaveated praise is the more dangerous half because
    a CDE has no reason to go looking behind good news. 1.5.1 answered that by
    attaching the same basis to both directions, and this test asserted the
    strength string still carried it.

    WHY IT COULD NOT SURVIVE UNCHANGED. T1 withdrew ``_identify_strengths``
    entirely, so there is no strength string left to carry a basis. The old
    assertion — "the diverse fixture emits no geographic strength, so this
    gate is vacuous" — would now fire on the FIX rather than on a regression.

    WHY IT IS NOT DELETED. Deleting it would remove the only assertion in the
    suite that the diverse shipped fixture reaches this ground at all, and a
    2.0.0 that re-introduced a strengths list would find nothing red here. The
    property asserted is now the stronger one: on the fixture that used to
    produce the uncaveated praise, NOTHING is asserted in either direction.
    """
    app = Application(cde=CDEProfile.sample(), requested_allocation=65_000_000)
    app.add_pipeline(Pipeline.sample(n=20))
    analysis = app.analyze()
    score = compute_readiness_score(
        analysis.pipeline_result, analysis.validation_results
    )

    # The fixture must still reach the ground F4 was about, or this is vacuous
    # for a second and different reason.
    assert score.component_scores["geographic_diversity"] >= 70, (
        "Pipeline.sample(n=20) no longer clears the old strength gate of 70, "
        "so this test no longer stands where F4's defect stood."
    )
    assert score.top_strengths == [], (
        "the readiness composite emitted a strength. T1 withdrew the strengths "
        f"list; anything here is a re-introduction:\n  {score.top_strengths}"
    )
    assert score.top_weaknesses == [], (
        "the readiness composite emitted a weakness. T1 withdrew the "
        f"weaknesses list:\n  {score.top_weaknesses}"
    )


# ---------------------------------------------------------------------------
# FIX 2 + FIX 5 — the docs text, and B2's published page
#
# TWO SWEEPS EACH MISSED SITES THE NEXT ONE FOUND. T2 swept and found
# why.md; the 1.5.1 audit swept and found recommendations.md, live on gh-pages
# and stronger than anything withdrawn. A third sweep found four more:
# optimization.md's constraint comments, quickstart.md's engine description,
# visualizations.md's radar section, and an annotation drawn onto a PNG by
# visualization/maps.py.
#
# A sweep that has to be repeated by hand is a sweep that will be skipped. This
# is the sweep as an assertion.
# ---------------------------------------------------------------------------

#: Phrases that assert something about a population of past Allocatees. Every
#: WINNER_* key in this package is registered HOUSE and unsourced, so any of
#: these standing as an assertion is a claim with no referent.
_WINNER_POPULATION_CLAIMS = (
    "winner p25",
    "winner median",
    "winner distribution",
    "winners typically",
    "historically correlate with non-funding",
    "blocks competitive consideration",
    "not viable in current form",
    "will be penalized relative to competitors",
)

#: A page may DISCUSS a withdrawn claim — that is what a withdrawal notice IS.
#: The same allowance test_121_financial_tables makes, and for the same reason.
_WITHDRAWAL_MARKERS = (
    "withdrawn", "deleted", "removed", "no longer", "corrected",
    "does not exist", "used to", "previously", "stood here", "read:",
    "unsourced", "house", "must not be added back",
)


def _is_quotation(block: str) -> bool:
    """A markdown blockquote is quoted material, not the page's assertion.

    Every line of the block starts with ``>``. That is how this documentation
    set already renders a withdrawn claim it needs to show the reader -- see
    ``about/why.md`` -- so treating it as an assertion would forbid quoting the
    very strings these gates exist to keep out of the prose.
    """
    lines = [ln for ln in block.strip().splitlines() if ln.strip()]
    return bool(lines) and all(ln.lstrip().startswith(">") for ln in lines)

_DOCS_ROOT = os.path.join(_REPO_ROOT, "docs")


def _markdown_pages():
    pages = []
    for dirpath, _dirs, names in os.walk(_DOCS_ROOT):
        if "hooks" in dirpath:
            continue
        for name in sorted(names):
            if name.endswith(".md"):
                pages.append(os.path.join(dirpath, name))
    return pages


def _paragraphs(text):
    """Split into the smallest unit a claim and its correction genuinely share.

    A MARKER FOR ONE CLAIM MUST NOT EXCUSE ANOTHER (1.5.1 audit). The first
    version of this split on blank lines only, which put every bullet of a list
    into ONE block -- so a sibling bullet reading "this tool's own **HOUSE**
    reference bands" excused an unrelated bullet asserting "the winner median"
    three lines below it.

    That is F3's defect exactly, one level up: the gate matched a disclosure to
    a claim by PROXIMITY rather than by subject, and was therefore satisfied by
    a disclosure about something else. It was caught by reverting a docs fix and
    finding the gate still green -- the same reversion that caught F3.

    Each markdown list item is now its own unit, so a bullet must carry its own
    marker.
    """
    units = []
    for block in re.split(r"\n\s*\n", text):
        lines = block.splitlines()
        if not any(re.match(r"\s*[-*+]\s|\s*\d+\.\s", ln) for ln in lines):
            units.append(block)
            continue
        current = []
        for line in lines:
            if re.match(r"\s*[-*+]\s|\s*\d+\.\s", line) and current:
                units.append("\n".join(current))
                current = [line]
            else:
                current.append(line)
        if current:
            units.append("\n".join(current))
    return units


@pytest.mark.skipif(
    not os.path.isdir(_DOCS_ROOT),
    reason="docs/ absent — an unpacked sdist prunes it",
)
def test_no_docs_page_asserts_a_winner_population_claim():
    """FIX 2 + FIX 5. The third sweep, as a gate.

    A winner-population phrase is allowed only inside a block that also marks
    it as withdrawn or unsourced. Restoring "The goal is to reach at least the
    winner p25 of 4 states, ideally 7+ states" to recommendations.md — the
    string that was live on gh-pages at 4bd26ab — turns this red.
    """
    failures = []
    for path in _markdown_pages():
        with io.open(path, encoding="utf-8") as handle:
            text = handle.read()
        rel = os.path.relpath(path, _REPO_ROOT)
        for block in _paragraphs(text):
            low = block.lower()
            hits = [p for p in _WINNER_POPULATION_CLAIMS if p in low]
            if not hits:
                continue
            if _is_quotation(block):
                continue
            if any(marker in low for marker in _WITHDRAWAL_MARKERS):
                continue
            failures.append(
                f"  {rel}: {hits} asserted with no withdrawal or HOUSE "
                f"marker in the same block:\n      {block.strip()[:220]}"
            )
    assert not failures, (
        "Documentation pages assert claims about a population of past NMTC "
        "Allocatees. This package holds no such population: every WINNER_* key "
        "is registered HOUSE and unsourced.\n\n"
        "A page may DISCUSS a withdrawn claim — say so in the same block.\n\n"
        + "\n".join(failures)
    )


@pytest.mark.skipif(
    not os.path.isdir(_DOCS_ROOT),
    reason="docs/ absent — an unpacked sdist prunes it",
)
def test_no_docs_page_instructs_the_reader_to_add_states():
    """FIX 5. The B2 blocker, and the class it belongs to.

    ``docs/workflow/recommendations.md`` was published saying "The goal is to
    reach at least the winner p25 of 4 states, ideally 7+ states" and that only
    one state "Blocks competitive consideration" — the withdrawn advice, in
    stronger terms than the string that was withdrawn, on the page that was the
    load-bearing defence for withdrawing it.
    """
    failures = []
    for path in _markdown_pages():
        with io.open(path, encoding="utf-8") as handle:
            text = handle.read()
        rel = os.path.relpath(path, _REPO_ROOT)
        for block in _paragraphs(text):
            low = block.lower()
            hits = [p for p in _WITHDRAWN_INSTRUCTIONS if p in low]
            if not hits:
                continue
            if _is_quotation(block):
                continue
            if any(marker in low for marker in _WITHDRAWAL_MARKERS):
                continue
            failures.append(f"  {rel}: {hits}\n      {block.strip()[:220]}")
    assert not failures, (
        "Documentation instructs a CDE toward a metric the CDFI Fund does not "
        "score, in a direction that costs points on metrics it does:\n"
        + "\n".join(failures)
    )


@pytest.mark.skipif(
    not os.path.isdir(_DOCS_ROOT),
    reason="docs/ absent — an unpacked sdist prunes it",
)
def test_the_recommendations_page_does_not_document_categories_the_engine_cannot_emit():
    """FIX 5, second half — the page was false about the code, not only unsourced.

    ``recommendations.md`` documented five categories (`distress`,
    `geographic`, `impact`, `sector`, `pipeline`). ``RecommendationEngine``
    emits three, and none of the five strings is among them. A reader filtering
    ``rec.category == "geographic"`` got an empty list and no error.

    Derived from the source, so adding a category to the engine does not
    silently make this stale.
    """
    engine = os.path.join(_REPO_ROOT, "nmtcapp", "intelligence", "recommendations.py")
    if not os.path.exists(engine):
        pytest.skip("package source absent (installed tree, not a checkout)")
    with io.open(engine, encoding="utf-8") as handle:
        emitted = set(re.findall(r'category="([a-z_]+)"', handle.read()))
    assert emitted, "no categories found in the engine — this gate is vacuous"

    page = os.path.join(_DOCS_ROOT, "workflow", "recommendations.md")
    with io.open(page, encoding="utf-8") as handle:
        text = handle.read()

    # ONLY the "## Categories" section. The page has several tables of
    # backticked identifiers -- priorities, field names -- and sweeping all of
    # them would flag `critical`/`high`/`medium`, which are priorities and are
    # correctly documented. A sweep whose corpus is wrong reports a defect that
    # is not there, which is how a gate gets widened until it asserts nothing.
    section = re.search(
        r"^##\s+Categories\b(.*?)(?=^##\s|\Z)", text, re.MULTILINE | re.DOTALL
    )
    assert section, (
        "recommendations.md has no '## Categories' section — this gate has "
        "lost its corpus and would adjudicate nothing."
    )
    documented = set(re.findall(r"^\|\s*`([a-z_]+)`\s*\|", section.group(1),
                                re.MULTILINE))
    assert documented, "the Categories section documents no categories"
    phantom = documented - emitted
    assert not phantom, (
        f"recommendations.md documents categories the engine cannot emit: "
        f"{sorted(phantom)}.\nThe engine emits: {sorted(emitted)}."
    )


def test_the_recommendation_engine_emits_no_geographic_advice_at_any_state_count():
    """FIX 5's premise, executed rather than asserted.

    THIS IS THE LOAD-BEARING CLAIM OF THE WHOLE SUPPRESSION. T1 withdrew the
    readiness engine's geographic advice on the stated grounds that
    ``intelligence.RecommendationEngine`` "emits no geographic advice at all",
    so a CDE is not left without guidance. That claim was true of the code and
    false of the published docs for that code.

    It is now executed at every state count from one to five. If this engine
    ever starts emitting geographic advice, the suppression's justification has
    changed and somebody must rule on it again.
    """
    pattern = re.compile(
        r"geograph|\bstates?\b|footprint|hhi|concentrat", re.IGNORECASE
    )
    for label in ("one_state", "two_states", "three_states",
                  "four_states", "six_states_conc"):
        app = _pipeline(_SHAPES[label])
        recs = app.recommendations()
        hits = []
        for rec in recs.recommendations:
            blob = " ".join([
                rec.category, rec.finding, rec.action,
                rec.expected_impact, rec.quantified_improvement,
            ])
            if pattern.search(blob):
                hits.append(f"[{rec.priority}] {rec.category}: {rec.finding[:140]}")
        assert not hits, (
            f"{label}: RecommendationEngine emitted geographic advice.\n"
            "T1's suppression of the OTHER engine's geographic advice rests on "
            "this engine emitting none — see readiness_score."
            "_build_recommendations. That premise no longer holds:\n"
            + "\n".join(f"  - {h}" for h in hits)
        )


# ---------------------------------------------------------------------------
# FIX 4 — the Streamlit rendering (F1)
# ---------------------------------------------------------------------------

_STREAMLIT_PAGES = os.path.join(_REPO_ROOT, "streamlit_app", "pages")


@pytest.mark.skipif(
    not os.path.isdir(_STREAMLIT_PAGES),
    reason="streamlit_app/ absent (installed tree, not a checkout)",
)
def test_no_streamlit_metric_passes_a_classification_as_a_delta():
    """FIX 4. The defect T4 half-fixed, asserted as a property.

    ``st.metric``'s ``delta`` means "this value moved, in this direction".
    Streamlit derives the arrow's DIRECTION from the delta's sign BEFORE it
    consults ``delta_color``, so a string with no sign always renders with an
    UP arrow and no argument removes it — which is why T4's
    ``delta_color="off"`` fixed the colour and left the arrow.

    A delta is legitimate only when the string carries a sign. This asserts
    that every ``delta=`` in the app is either an f-string with an explicit
    ``:+`` sign conversion, or is not a delta at all.
    """
    offenders = []
    for name in sorted(os.listdir(_STREAMLIT_PAGES)):
        if not name.endswith(".py"):
            continue
        path = os.path.join(_STREAMLIT_PAGES, name)
        with io.open(path, encoding="utf-8") as handle:
            lines = handle.readlines()
        for number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#") or "delta=" not in stripped:
                continue
            # A signed numeric movement is what the slot is for.
            if ":+" in stripped:
                continue
            offenders.append(f"  streamlit_app/pages/{name}:{number}: {stripped}")
    assert not offenders, (
        "st.metric received a delta that carries no sign. Streamlit will draw "
        "an UP arrow beside it whatever delta_color says — a grade, a verdict, "
        "a section label or a denominator rendered as favourable movement.\n\n"
        "Use utils.metric_classification() instead: it renders the "
        "classification below the metric, where it has no direction.\n\n"
        + "\n".join(offenders)
    )


@pytest.mark.skipif(
    not os.path.isdir(_STREAMLIT_PAGES),
    reason="streamlit_app/ absent (installed tree, not a checkout)",
)
def test_delta_color_is_never_selected_by_the_sign_of_its_own_delta():
    """FIX 4's sibling, found by the same sweep.

    ``3_Pipeline_Optimizer`` chose ``delta_color="normal" if delta >= 0 else
    "inverse"``. "normal" renders UP green; "inverse" renders DOWN green — so
    selecting the mode BY THE SIGN painted the delta green in both branches,
    and an optimizer run that LOWERED the score reported the drop in green.

    A conditional that cancels the distinction the argument exists to draw.
    """
    offenders = []
    for name in sorted(os.listdir(_STREAMLIT_PAGES)):
        if not name.endswith(".py"):
            continue
        path = os.path.join(_STREAMLIT_PAGES, name)
        with io.open(path, encoding="utf-8") as handle:
            lines = handle.readlines()
        pattern = re.compile(
            r'delta_color\s*=\s*"normal"\s+if\s+.*?\s+else\s+"inverse"'
        )
        for number, line in enumerate(lines, start=1):
            # A comment EXPLAINING the defect is not the defect. This module
            # records why the conditional was wrong, and a sweep that cannot
            # tell an explanation from an occurrence forces the explanation to
            # be deleted -- which is how the reason for a fix gets lost.
            if line.lstrip().startswith("#"):
                continue
            match = pattern.search(line)
            if match:
                offenders.append(
                    f"  streamlit_app/pages/{name}:{number}: {match.group(0)}"
                )
    assert not offenders, (
        "delta_color is being selected by the sign of the delta it colours. "
        "Both branches render green, so the colour carries no information:\n"
        + "\n".join(offenders)
    )


def test_streamlit_off_does_not_remove_the_arrow_which_is_why_the_fix_changed():
    """THE EXECUTED BASIS FOR F1, pinned so the claim cannot go stale.

    1_Pipeline_Analyzer.py and CHANGELOG.md both stated that
    ``delta_color="off"`` yields GRAY/NONE. It does not: it yields GRAY/UP for
    any unsigned string. This drives Streamlit's own function so that if a
    future Streamlit ever DOES suppress the arrow, this test says so instead of
    the package carrying a stale justification.
    """
    streamlit = pytest.importorskip("streamlit")
    try:
        from streamlit.elements.metric import (
            _determine_delta_color_and_direction as determine,
        )
        from streamlit.proto.Metric_pb2 import Metric as proto
    except ImportError:  # pragma: no cover - Streamlit internals moved
        pytest.skip(
            f"Streamlit {streamlit.__version__} no longer exposes "
            "_determine_delta_color_and_direction; re-derive F1's basis "
            "against the new internals before trusting the comment in "
            "1_Pipeline_Analyzer.py"
        )

    directions = {v: k for k, v in proto.MetricDirection.items()}
    colours = {v: k for k, v in proto.MetricColor.items()}

    for grade in "ABCDF":
        result = determine("off", f"Grade {grade}")
        assert directions[result.direction] == "UP", (
            f"Streamlit {streamlit.__version__} now returns "
            f"{directions[result.direction]} for delta_color='off' with an "
            f"unsigned delta. F1's reasoning — that no delta_color removes the "
            "arrow, so a grade must not be a delta — should be re-derived."
        )
        assert colours[result.color] == "GRAY", result

    # The control: an empty delta is the only thing that yields NONE, and it is
    # why the fix is "do not pass a delta" rather than "pass a different one".
    empty = determine("off", "")
    assert directions[empty.direction] == "NONE", empty
