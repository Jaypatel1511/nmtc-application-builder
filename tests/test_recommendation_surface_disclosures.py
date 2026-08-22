"""THE RECOMMENDATIONS SURFACE IS A SURFACE, AND TWO GATES DID NOT KNOW IT.

T1 -- WHICH ROUND. ``RecommendationSet.summary()`` cites the CY 2024-2025
Review Process thirteen times on a single run and says nothing about that round
being closed. Measured on the corpus this module builds: ``CY 2024-2025`` 13
hits, ``CY 2026`` 0, ``not open`` 0, ``superseded`` 0, ``no longer`` 0,
``governing`` 0, ``most recent published`` 0.

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
        application_round="CY2025",
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


#: Streamlit pages that cite the round in their own source. These are rendered
#: surfaces the ``generate()`` format list cannot see.
_STREAMLIT_PAGES = (
    "streamlit_app/pages/2_Win_Alignment_Scorer.py",
    "streamlit_app/pages/4_About_and_Methodology.py",
)


@pytest.mark.parametrize("relpath", _STREAMLIT_PAGES)
def test_a_streamlit_page_that_cites_the_round_renders_its_provenance(relpath):
    """A page naming a closed round must carry the note, not just the citation.

    Source-level, because a Streamlit page is not importable as a renderer.
    The assertion is that the page CALLS the shared helper -- asserting on the
    rendered words instead would let a page pass by retyping them, which is the
    defect one layer out.
    """
    path = os.path.join(_REPO_ROOT, relpath)
    with open(path, encoding="utf-8") as handle:
        source = handle.read()

    assert rp.CITED_ROUND in source, f"precondition: {relpath} cites the round"
    # THE FUNCTION, NOT THE MODULE NAME. Asserting on "round_provenance" alone
    # passed 4_About_and_Methodology.py, which mentions the module in PROSE at
    # line 451 and renders none of it -- a gate satisfied by a comment is the
    # gate-that-cannot-fail shape this repository keeps recording.
    assert "round_provenance_paragraphs" in source or "round_provenance_note" in source, (
        f"{relpath} cites {rp.CITED_ROUND} {source.count(rp.CITED_ROUND)} times "
        f"and never renders its provenance. It is {rp.CITED_ROUND_STATUS}, and "
        f"{rp.UPCOMING_ROUND} is not open. Render "
        "nmtcapp.renderers._round_provenance.round_provenance_paragraphs()."
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
