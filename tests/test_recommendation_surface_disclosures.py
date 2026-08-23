"""THE RECOMMENDATIONS SURFACE IS A SURFACE, AND TWO GATES DID NOT KNOW IT.

T1 -- WHICH ROUND. ``RecommendationSet.summary()`` cited the CY 2024-2025
Review Process repeatedly on a single run and said nothing about that round
being closed.

THE HEADLINE COUNT THAT USED TO SIT HERE WAS NOT A MEASUREMENT OF ANY TREE
(1.5.4 audit close, N4). It read "13 hits, ``CY 2026`` 0" and presented that as
one run, but no single revision produces both halves: at 1.5.3 the fix is
absent, so ``CY 2026`` is genuinely 0 -- and ``CY 2024-2025`` is 1, not 13. The
pair described a before-state and an after-state stated as though they were one
observation, which is the shape a citation count is least able to survive.

RE-MEASURED, on the corpus this module actually builds
(``CDEProfile.sample()`` + ``Pipeline.sample(n=20)``), naming the revision:

    8a3b18b (v1.5.3)   CY 2024-2025  1    CY 2026  0    not open  0
    4fcfb5b (v1.5.4)   CY 2024-2025  2    CY 2026  2    not open  0

WHAT THE 13 WAS COUNTING COULD NOT BE ESTABLISHED, and it is not chased here:
the corpus depends on which items a CDE's score causes to render, and a
low-scoring profile emits far more citations than the sample one does. The
assertions below never read a count -- they test for the PRESENCE of the round,
its status and the upcoming round -- so nothing was gated on the wrong figure.
That is why this is a docstring correction and not a code change.

The round IS closed -- opened 19 Nov 2024, closed 29 Jan 2025, awarded
23 Dec 2025 at $10 billion -- and CY 2026 was announced 12 Aug 2026 at
$5 billion and is not open. ``renderers/_round_provenance`` has carried all of
that since 1.5.0, and markdown, Word, Excel and PDF all render it.
``RecommendationSet.summary()`` and the Streamlit Win Alignment Scorer did not,
because ``test_round_provenance._ALL_FORMATS`` lists the four ``generate()``
formats and a surface that is not a ``generate()`` format cannot appear in it.

That is the third time the same gap has been found by widening a surface list
by one notch (F2 for disclosures, 1.5.3 for frame geometry), and widening it
this time found a fourth instance immediately: ``4_About_and_Methodology.py``
cites the round FIFTEEN times and renders no provenance at all. It is asserted
here too.

T4 -- ELIGIBILITY PRECEDES RANKING. On an all-ineligible pipeline the engine
emitted thirteen items and not one of them said the pipeline was ineligible.
The items advise on improving rank *within the Highly Qualified pool*.

LIC status is not a scored band. IRC section 45D(d) requires each QLICI to be
made in a qualified active low-income community business located in a
Low-Income Community; QEI attributed to a tract that is not a LIC cannot count
toward the substantially-all test at Treas. Reg. section 1.45D-1(c)(5)(i). No
amount of ranking improvement reaches a project in a tract that does not
qualify.

THE RULING, and it is the weaker of the two available ones ON PURPOSE. The fact
goes ABOVE the items; the items still render. Suppressing them was considered
and rejected: most of them are about the CDE (track record, board composition,
DBC focus) and remain true and actionable whatever the pipeline's tracts say,
and withdrawing them would leave a CDE with a failed gate and no guidance at
all -- the "overstating uncertainty" direction of error that
``_round_provenance`` names, where a correct fact leads somewhere worse than
the error it replaced. What ranking advice may not do is arrive FIRST, or
alone, so the gate item is emitted first and the overall assessment names it.
"""
from __future__ import annotations

import ast
import os
import re

import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline
from nmtcapp.intelligence.recommendations import RecommendationEngine
from nmtcapp.renderers import _round_provenance as rp

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _app(pipeline=None, cde=None) -> Application:
    app = Application(
        cde=cde or CDEProfile.sample(),
        requested_allocation=65_000_000,
        application_round="CY 2026",
    )
    app.add_pipeline(pipeline or Pipeline.sample(n=20))
    return app


def _ineligible_pipeline(n: int = 10) -> Pipeline:
    pipeline = Pipeline.sample(n=n)
    for project in pipeline:
        project.is_nmtc_eligible = False
        project.distress_level = "ineligible"
    return pipeline


def _flat(text: str) -> str:
    return " ".join(text.split())


# ---------------------------------------------------------------------------
# T1 -- the round, on the recommendations surface
# ---------------------------------------------------------------------------

def test_the_recommendations_summary_states_which_round_it_scores():
    """The surface cites a closed round thirteen times and never says so."""
    summary = _flat(_app().recommendations().summary())

    assert rp.CITED_ROUND in summary, "precondition: the surface cites the round"
    assert rp.CITED_ROUND_STATUS in summary, (
        f"RecommendationSet.summary() cites {rp.CITED_ROUND} "
        f"{summary.count(rp.CITED_ROUND)} times and never says it is "
        f"{rp.CITED_ROUND_STATUS}. Render "
        "_round_provenance.round_provenance_paragraphs()[0]; do not retype it."
    )
    assert rp.UPCOMING_ROUND in summary, (
        f"the surface never names {rp.UPCOMING_ROUND}, which is the round a "
        "CDE reading it today is preparing for."
    )
    assert "NOT YET PUBLISHED" in summary, (
        "the surface does not say the CY 2026 materials do not exist yet."
    )


def test_the_round_note_on_the_recommendations_surface_is_not_retyped():
    """One source of truth, same as the other four formats."""
    summary = _app().recommendations().summary()
    first = rp.round_provenance_paragraphs()[0]
    assert _flat(first) in _flat(summary), (
        "the round note on the recommendations surface is not "
        "round_provenance_paragraphs()[0] verbatim. A second copy of this text "
        "is the shape _round_provenance was created to remove."
    )


#: THE PAGES DIRECTORY, WALKED -- not a hand-maintained list (1.5.4 audit
#: close, B3). This was a two-entry tuple naming
#: ``2_Win_Alignment_Scorer.py`` and ``4_About_and_Methodology.py``, and a
#: hand-maintained surface list is the exact shape whose widening found the
#: About-page defect in the first place. Walking the directory found a THIRD
#: instance immediately: ``1_Pipeline_Analyzer.py`` cites the closed round in
#: rendered markdown prose and rendered no provenance.
_STREAMLIT_PAGES_DIR = os.path.join(_REPO_ROOT, "streamlit_app", "pages")

#: The helpers a page may render the note through. Both are public names in
#: ``nmtcapp.renderers._round_provenance``.
_PROVENANCE_HELPERS = frozenset({
    "round_provenance_paragraphs", "round_provenance_note",
})


def _page_sources():
    """(relpath, source, tree) for every Streamlit page, in name order."""
    out = []
    for name in sorted(os.listdir(_STREAMLIT_PAGES_DIR)):
        if not name.endswith(".py"):
            continue
        path = os.path.join(_STREAMLIT_PAGES_DIR, name)
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        rel = f"streamlit_app/pages/{name}"
        out.append((rel, source, ast.parse(source, filename=name)))
    return out


def _cites_round_in_rendered_text(tree) -> int:
    """How many times the page cites the round in TEXT A READER SEES.

    STRING LITERALS ONLY, and that is the whole point. The precondition used to
    be ``CITED_ROUND in source``, which is a search over the file including its
    comments -- so a page could acquire the precondition from a ``#`` line
    nobody renders. ``1_Pipeline_Analyzer.py`` has one of each: a citation in a
    comment at line 796 that no reader sees, and a citation in a rendered
    markdown string that every reader does.

    It also sees MORE than a source search can. Page 1's rendered citation is
    split across two source lines by implicit concatenation, so the characters
    ``CY 2024-2025`` never appear contiguously in the file at all; ``grep``
    cannot find it and ``ast`` can, because the parser joins the parts.
    """
    total = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            total += node.value.count(rp.CITED_ROUND)
    return total


def _provenance_calls(tree):
    """Every ``ast.Call`` node that CALLS a provenance helper, with its line.

    AN ACTUAL CALL NODE, NOT A SUBSTRING (1.5.4 audit close, B3). This gate has
    now been narrowed twice and stayed open both times, because both narrowings
    were string searches over source: first from the module name to the
    function name, and the function name is still satisfied by a comment. A
    hostile pass deleted the import and the render from
    ``2_Win_Alignment_Scorer.py``, left ``pass  # round_provenance_paragraphs``
    behind, and the full suite stayed green -- 1,408 passed. The same mutation
    on ``4_About_and_Methodology.py`` with a ``TODO`` comment did too.

    A comment is not a call. The AST does not carry comments at all, so this
    formulation cannot be satisfied by one -- which is a property of the
    representation rather than a cleverer pattern, and that is why it is the
    third narrowing and not a fourth.
    """
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr
        else:
            continue
        if name in _PROVENANCE_HELPERS:
            found.append((name, node.lineno))
    return found


@pytest.mark.skipif(
    not os.path.isdir(_STREAMLIT_PAGES_DIR),
    reason="streamlit_app/ absent (installed tree, not a checkout)",
)
def test_every_streamlit_page_that_cites_the_round_renders_its_provenance():
    """A page naming a closed round must carry the note, not just the citation.

    Source-level, because a Streamlit page is not importable as a renderer.
    The assertion is that the page CALLS the shared helper -- asserting on the
    rendered words instead would let a page pass by retyping them, which is the
    defect one layer out.

    Every page is examined and every offender is reported, rather than the
    first one failing and hiding the rest.
    """
    pages = _page_sources()
    assert pages, "no Streamlit pages found; this gate is asserting nothing"

    citing, offenders = [], []
    for rel, _source, tree in pages:
        hits = _cites_round_in_rendered_text(tree)
        if not hits:
            continue
        citing.append(rel)
        if not _provenance_calls(tree):
            offenders.append(f"  {rel} — cites {rp.CITED_ROUND} {hits}x in "
                             f"rendered text, calls no provenance helper")

    assert citing, (
        "no Streamlit page cites the round in rendered text. Either the "
        "citations moved or this gate stopped being able to see them; both "
        "mean it is no longer asserting anything."
    )
    assert not offenders, (
        f"{len(offenders)} Streamlit page(s) cite {rp.CITED_ROUND} in text a "
        f"reader sees and render no provenance. It is "
        f"{rp.CITED_ROUND_STATUS}, and {rp.UPCOMING_ROUND} is not open. Call "
        "nmtcapp.renderers._round_provenance.round_provenance_paragraphs():"
        "\n" + "\n".join(offenders)
    )


@pytest.mark.skipif(
    not os.path.isdir(_STREAMLIT_PAGES_DIR),
    reason="streamlit_app/ absent (installed tree, not a checkout)",
)
def test_a_mentioned_helper_is_not_a_rendered_one():
    """The mutation that survived twice, asserted as a property of the tree.

    For every page that renders the note, the helper must appear as an
    ``ast.Call``. Deleting the call and leaving the NAME behind -- in a
    comment, a docstring, a ``TODO``, or a bare attribute reference -- must not
    satisfy this gate, and cannot, because none of those parses to a Call node.
    """
    rendering = [(rel, source, tree) for rel, source, tree in _page_sources()
                 if _cites_round_in_rendered_text(tree)]
    assert rendering, "precondition: at least one page cites the round"

    for rel, source, tree in rendering:
        calls = _provenance_calls(tree)
        mentions = sum(source.count(h) for h in _PROVENANCE_HELPERS)
        assert calls, (
            f"{rel} mentions a provenance helper {mentions} time(s) in its "
            "source and CALLS one zero times. A name in a comment is not a "
            "render; this gate was satisfied by exactly that shape twice."
        )


# ---------------------------------------------------------------------------
# T4 -- eligibility precedes ranking
# ---------------------------------------------------------------------------

def test_an_ineligible_pipeline_is_told_that_it_is_ineligible():
    recs = _app(pipeline=_ineligible_pipeline()).recommendations()
    corpus = _flat(recs.summary())

    assert "not a Low-Income Community" in corpus or "NOT NMTC-ELIGIBLE" in corpus, (
        "every project in this pipeline sits in a tract that is not a "
        "Low-Income Community, and no recommendation says so. The items advise "
        "on rank within the Highly Qualified pool.\n\n" + corpus[:1500]
    )
    assert "45D(d)" in corpus, (
        "the gate is statutory and the item does not cite the statute. A house "
        "framing of a federal requirement is how this package has previously "
        "shipped a bar that does not exist."
    )


def test_the_eligibility_gate_is_the_first_item_a_cde_reads():
    """Ranking advice below a failed gate is not advice, so it may not lead."""
    recs = _app(pipeline=_ineligible_pipeline()).recommendations()
    assert recs.recommendations, "no recommendations at all"
    first = recs.recommendations[0]
    assert "Low-Income Community" in first.finding, (
        "the first item a CDE reads on an ineligible pipeline is "
        f"{first.finding[:120]!r}. Eligibility precedes ranking."
    )
    assert first.priority == "critical", first.priority


def test_the_overall_assessment_names_the_failed_gate():
    recs = _app(pipeline=_ineligible_pipeline()).recommendations()
    assert "eligib" in recs.overall_assessment.lower(), (
        "the assessment reports a tier and a gap to the Highly Qualified "
        "aggregate without saying the pipeline fails the statutory LIC gate:\n"
        + recs.overall_assessment
    )


def test_a_fully_eligible_pipeline_is_not_told_it_failed_a_gate():
    """The other direction: the gate must not fire on a clean pipeline."""
    app = _app()
    assert app.analyze().pipeline_result.eligibility_pct == 1.0, "precondition"
    corpus = _flat(app.recommendations().summary())
    assert "45D(d)" not in corpus, (
        "the eligibility gate fired on a pipeline that is 100% eligible:\n"
        + corpus[:1000]
    )


def test_unverified_eligibility_is_not_reported_as_ineligibility():
    """A tract nobody could check is not a tract that failed.

    ``eligibility_pct`` counts ``is_nmtc_eligible is True``, so it is 0.0 BOTH
    when every project is confirmed ineligible and when nothing could be
    determined. A gate built on that number cannot tell the two apart, and
    reporting the second as a failed statutory gate would be a fabricated
    negative -- the defect ``_score_pipeline_credibility``'s
    ``skip_eligibility_penalty`` already guards one layer down.

    THE FIXTURE MOVES THE DOLLARS, IT DOES NOT ASK THE MAPPER TO FAIL. Setting
    ``distress_level = None`` on the projects does not survive
    ``Application.analyze()``: the mapper enriches them and returns real
    answers, so the pipeline comes back 100% eligible. (That is how the first
    draft of this test came to SKIP rather than run, which is a gate that has
    stopped asking.) So the undetermined state is built where the gate reads
    it: the confirmed-ineligible QEI is moved into ``unknown``, which is where
    ``analyze_distress_concentration`` puts a project whose distress level is
    ``None``, and ``eligibility_pct`` is left at 0.0 so the naive measure would
    still fire.
    """
    app = _app(pipeline=_ineligible_pipeline())
    result = app.analyze().pipeline_result
    win_score = app.score_win_probability()

    buckets = dict(result.distress_breakdown["dollars_by_distress"])
    counts = dict(result.distress_breakdown.get("project_count_by_distress", {}))
    assert buckets.get("ineligible", 0) > 0, "precondition: nothing to move"
    buckets["unknown"] = buckets.get("unknown", 0) + buckets["ineligible"]
    counts["unknown"] = counts.get("unknown", 0) + counts.get("ineligible", 0)
    buckets["ineligible"] = 0
    counts["ineligible"] = 0
    result.distress_breakdown = {
        **result.distress_breakdown,
        "dollars_by_distress": buckets,
        "project_count_by_distress": counts,
    }
    assert result.eligibility_pct == 0.0, "precondition: still reads 0% eligible"

    recs = RecommendationEngine().recommend(result, None, win_score)
    corpus = _flat(recs.summary())
    assert "45D(d)" not in corpus, (
        "an UNVERIFIED pipeline was reported as failing the statutory LIC "
        "gate. Unknown is not ineligible.\n\n" + corpus[:1200]
    )
    assert "eligib" not in _flat(recs.overall_assessment).lower(), (
        "the assessment's eligibility qualifier fired on undetermined tracts."
    )


def test_a_degraded_eligibility_run_does_not_report_a_failed_gate():
    """The other unverified state: the eligibility dataset would not load.

    ``eligibility_data_status != "ok"`` means the run could not determine
    anything, and the gate returns before it looks at a bucket at all.
    """
    app = _app(pipeline=_ineligible_pipeline())
    result = app.analyze().pipeline_result
    win_score = app.score_win_probability()
    assert result.distress_breakdown["dollars_by_distress"]["ineligible"] > 0
    result.eligibility_data_status = "unavailable"

    corpus = _flat(RecommendationEngine().recommend(result, None, win_score).summary())
    assert "45D(d)" not in corpus, (
        "a run whose eligibility data would not load was reported as failing "
        "the statutory LIC gate.\n\n" + corpus[:1200]
    )


# ---------------------------------------------------------------------------
# B2 (1.5.4 audit close) -- a non-zero share may never render as 0%
# ---------------------------------------------------------------------------

def _one_small_ineligible_pipeline(qei: int = 50_000) -> Pipeline:
    """One tiny ineligible project among a pipeline of eligible ones.

    THE SHAPE THAT BROKE IT. Every other fixture in this module drives the
    eligibility gate with an ALL-ineligible pipeline, where the share is 100%
    and every ``:.0%`` render is true. The defect lives at the other end: a
    share small enough to round to zero. $50,000 in a $114,050,000 pipeline is
    0.0438%, which is the realistic case -- one project in a real CDE's
    pipeline whose tract turns out not to qualify.

    Left pre-enriched (``Pipeline.sample`` ships verified eligibility data), so
    this reaches no network and no mapper.
    """
    pipeline = Pipeline.sample(n=20)
    projects = list(pipeline)
    for project in projects:
        project.is_nmtc_eligible = True
        if project.distress_level in (None, "", "ineligible", "unknown"):
            project.distress_level = "severe"
    projects[0].is_nmtc_eligible = False
    projects[0].distress_level = "ineligible"
    projects[0].qei_request = qei
    return pipeline


def test_a_tiny_ineligible_share_is_never_rendered_as_zero_percent():
    """B2. RED against 4fcfb5b on both surfaces.

    THE DEFECT. T4 added three ``:.0%`` renders and floored none of them. On
    this pipeline all three printed ``0%``, and the ASSESSMENT sentence carried
    no project count at all -- so on the surface a CDE reads first, the
    sentence was ``0% of pipeline QEI is in tracts that are not a Low-Income
    Community``: unqualified, and false.

    ``0%`` and ``no ineligible QEI`` are the same words to a reader, and the
    two states could not be more different: one is a pipeline that passes the
    statutory gate, the other is a pipeline that does not.
    """
    app = _app(pipeline=_one_small_ineligible_pipeline())
    result = app.analyze().pipeline_result
    buckets = result.distress_breakdown["dollars_by_distress"]

    ineligible = buckets["ineligible"]
    total = result.total_qei_request
    assert 0 < ineligible / total < 0.005, (
        "precondition: the ineligible share must be small enough that a "
        f"``:.0%`` render rounds it to zero; it is {ineligible / total:.4%}"
    )

    recs = app.recommendations()
    gate = [r for r in recs.recommendations
            if "not a Low-Income Community" in r.finding]
    assert gate, "precondition: the eligibility gate item fired"

    surfaces = {
        "the gate item's finding": _flat(gate[0].finding),
        "the overall assessment": _flat(recs.overall_assessment),
        "the rendered summary": _flat(recs.summary()),
    }
    for name, text in surfaces.items():
        assert "0% of pipeline QEI" not in text, (
            f"{name} states that 0% of pipeline QEI is in a tract that is not "
            f"a Low-Income Community, on a pipeline whose ineligible share is "
            f"{ineligible / total:.4%} -- ${ineligible:,.0f} of "
            f"${total:,.0f}. A non-zero share may not render as zero: the "
            "sentence is read as 'none', and none is the one thing it is "
            f"not.\n\n{text[:900]}"
        )


def test_every_surface_that_states_the_share_also_states_the_count():
    """B2 rule 2. A share alone cannot distinguish TINY from NONE.

    The gate ITEM has carried ``(1 of 20 projects)`` since T4. The assessment
    sentence did not, and it is the one a CDE reads first -- so the surface
    most likely to be read alone was the surface with the least to read the
    percentage against.
    """
    app = _app(pipeline=_one_small_ineligible_pipeline())
    recs = app.recommendations()
    assessment = _flat(recs.overall_assessment)

    assert "ELIGIBILITY FIRST" in assessment, "precondition: the qualifier fired"
    assert re.search(r"\(1 of \d+ projects\)", assessment), (
        "the assessment states a share of pipeline QEI and no project count. "
        "A reader cannot tell one small project from a rounding artifact, and "
        "this is a DISCLOSURE of what was measured -- it sits inside the "
        f"principle T2 adopted, not against it.\n\n{assessment}"
    )


def test_a_partial_share_is_never_rendered_as_one_hundred_percent():
    """THE MIRROR THE AUDIT DID NOT NAME, and it is the same rounding.

    ``f"{0.996:.0%}"`` is ``"100%"``. A pipeline carrying one small ELIGIBLE
    project among nineteen ineligible ones would state that 100% of its QEI
    sits in a tract that does not qualify -- false in the direction that tells
    a CDE its entire pipeline is dead when part of it is not.

    Closed with the same floor rather than left for the round that trips over
    it, because it is one branch of the same helper.
    """
    pipeline = Pipeline.sample(n=20)
    projects = list(pipeline)
    for project in projects:
        project.is_nmtc_eligible = False
        project.distress_level = "ineligible"
    projects[0].is_nmtc_eligible = True
    projects[0].distress_level = "severe"
    projects[0].qei_request = 50_000

    app = _app(pipeline=pipeline)
    result = app.analyze().pipeline_result
    buckets = result.distress_breakdown["dollars_by_distress"]
    share = buckets["ineligible"] / result.total_qei_request
    assert 0.995 < share < 1.0, (
        f"precondition: the share must round UP to 100%; it is {share:.4%}"
    )

    recs = app.recommendations()
    corpus = _flat(recs.summary())
    assert "100% of pipeline QEI" not in corpus, (
        f"the surface states that 100% of pipeline QEI is in a tract that is "
        f"not a Low-Income Community, when the share is {share:.4%} and "
        f"${buckets['ineligible']:,.0f} of ${result.total_qei_request:,.0f} "
        "leaves a project that DOES qualify. Told its whole pipeline is "
        f"ineligible, a CDE withdraws a project it could have filed.\n\n"
        + corpus[:900]
    )
