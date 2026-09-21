"""Word and PDF stopped asserting what this package's own disclosure denies.

THE DEFECT (1.7.1 R11)
======================

On the partial-unverified path — the dataset loaded, but some projects could
not be location-verified — ``word_builder`` and ``pdf_builder`` ended the
Executive Summary's distress sentence with

    "— figures reflect location-verified projects only."

That asserts a VERIFIED-ONLY DENOMINATOR. ``renderers/_disclosure`` adjudicates
the opposite, in the banner printed four lines ABOVE that sentence in the same
document:

    "Distress and targeting shares count only location-verified projects in
     the numerator but ALL PIPELINE QEI IN THE DENOMINATOR, so each is a
     LOWER BOUND"

and its note records why the arithmetic is the half that stays: a verified-only
denominator "OVERSTATES, in the direction that flatters the applicant" — one
verified deep-distress project out of twenty would file "100% of QEI in
deep/severe tracts" — and "understating is the only safe direction to err in a
federal filing."

So one Word or PDF document carried the banner saying LOWER BOUND and, a page
earlier, a sentence saying the figure was computed the flattering way. The
claim was struck from the BANNER years ago; the fund-attribution allowlist
still records that banner as "text that used to claim the figures 'reflect
verified projects only'". It survived on two surfaces in the Executive Summary,
which is the one-surface-fixed shape this package keeps shipping from.

``markdown_builder`` already rendered the correct sentence. Word and PDF did
not get that fix.

WHY THE CLAUSE IS REWORDED AND NOT DELETED
==========================================

Deleting it was the other candidate. It is worse. The figure IS a lower bound;
the banner already says so; and an unqualified share standing beside a banner
is how a reader concludes the qualifier belongs to something else. The
disclosure module's own closing rule — "each figure states its own basis" — is
an argument for stating it beside the figure, not for removing it. The wording
is markdown's, moved into ``_disclosure.LOWER_BOUND_CLAUSE`` so all three
surfaces read one string rather than three that agree by luck; markdown's
rendered bytes do not move.

WHAT THIS GATE ASSERTS
======================

It renders the PARTIAL-UNVERIFIED branch, which a default render never reaches
— a gate reading the packaged fixture would see none of this. The fixture is
``tests/test_excel_geometry._analysis_in_state``, the shape
``test_headline_distress_denominator.test_the_partial_unverified_branch_states_it_too``
already uses.

Positive assertions are BOUNDED to the Executive Summary, because the lower-
bound language legitimately appears in the banner too and a document-wide
``assert "lower bound" in text`` would stay green with the sentence reverted.
The negative assertion — that the verified-only claim appears NOWHERE — is
deliberately document-wide: absence over a larger region is a stronger claim,
not a weaker one.
"""
from __future__ import annotations

import re

import pytest

from nmtcapp.renderers._disclosure import LOWER_BOUND_CLAUSE

#: The exact sentence endings that assert a verified-only denominator. The
#: first is what Word and PDF shipped through 1.7.0; the second is what the
#: banner itself said before it was corrected. Neither may reappear on any
#: surface, in any region.
FORBIDDEN_CLAIMS = (
    "reflect location-verified projects only",
    "reflect verified projects only",
)

#: What the banner must keep saying. R11 corrects a sentence that contradicted
#: the banner; a "fix" that instead softened the banner would satisfy the
#: consistency check and lose the disclosure, so the banner is pinned too.
BANNER_ANCHORS = (
    "all pipeline QEI in the denominator",
    "LOWER BOUND",
)

SURFACES = ("markdown", "word", "pdf")


@pytest.fixture(scope="module")
def partial(tmp_path_factory) -> dict:
    """The three flowing surfaces rendered on the partial-unverified path."""
    from nmtcapp.core.application import Application
    from nmtcapp.renderers.markdown_builder import MarkdownApplicationBuilder
    from nmtcapp.renderers.pdf_builder import PDFApplicationBuilder
    from nmtcapp.renderers.word_builder import WordApplicationBuilder
    from tests.test_excel_geometry import _analysis_in_state
    from tests.test_rendered_output_baseline import (
        APPLICATION_ROUND, REQUESTED_ALLOCATION, _cde, _pipeline,
    )

    app = Application(cde=_cde(), requested_allocation=REQUESTED_ALLOCATION,
                      application_round=APPLICATION_ROUND)
    app.add_pipeline(_pipeline())
    analysis = _analysis_in_state(app.analyze(), "partial_unverified")
    out = tmp_path_factory.mktemp("partial")
    paths = {
        "markdown": str(out / "a.md"),
        "word": str(out / "a.docx"),
        "pdf": str(out / "a.pdf"),
    }
    MarkdownApplicationBuilder(app, analysis).save(paths["markdown"])
    WordApplicationBuilder(app, analysis).save(paths["word"])
    PDFApplicationBuilder(app, analysis).save(paths["pdf"])
    return paths


def _summary(fmt: str, path: str) -> str:
    """The Executive Summary on one surface, flattened to one line.

    The extractor is ``test_headline_distress_denominator._executive_summary``
    — the same bounded region that module already proves it can read on all
    three surfaces. Imported rather than re-derived: two spellings of one
    boundary is how a bounded gate quietly stops being bounded.
    """
    from tests.test_headline_distress_denominator import _executive_summary

    return re.sub(r"\s+", " ", _executive_summary(fmt, path))


def _whole(fmt: str, path: str) -> str:
    if fmt == "markdown":
        text = open(path, encoding="utf-8").read()
    elif fmt == "word":
        import docx

        doc = docx.Document(path)
        text = "\n".join(p.text for p in doc.paragraphs)
        text += "\n" + "\n".join(
            cell.text for table in doc.tables
            for row in table.rows for cell in row.cells
        )
    else:
        from pypdf import PdfReader

        text = "\n".join((page.extract_text() or "")
                         for page in PdfReader(path).pages)
    return re.sub(r"\s+", " ", text)


@pytest.mark.parametrize("fmt", SURFACES)
def test_the_partial_summary_calls_the_figure_a_lower_bound(partial, fmt):
    """BOUNDED to the Executive Summary: the sentence states the lower bound.

    Bounded because the banner in the SAME section, and
    ``validation/readiness_score``'s note elsewhere in the document, also talk
    about lower bounds. A document-wide search would pass on either of them
    with this sentence reverted.
    """
    summary = _summary(fmt, partial[fmt])
    assert "unverified" in summary.lower(), (
        f"{fmt}: the fixture did not reach the partial-unverified branch, so "
        "everything below would be asserted about the wrong sentence"
    )
    assert LOWER_BOUND_CLAUSE in summary, (
        f"{fmt}: the Executive Summary's distress sentence does not say the "
        "figure is a lower bound. Expected "
        f"{LOWER_BOUND_CLAUSE!r}.\n\nRead: {summary!r}"
    )


@pytest.mark.parametrize("fmt", SURFACES)
def test_no_surface_claims_a_verified_only_denominator(partial, fmt):
    """DOCUMENT-WIDE, because this one is an absence.

    The numerator counts only verified projects and the denominator is all
    pipeline QEI. Any sentence saying the figures "reflect verified projects
    only" describes an arithmetic this package does not perform, and does so
    in the direction that flatters the applicant.
    """
    whole = _whole(fmt, partial[fmt])
    for claim in FORBIDDEN_CLAIMS:
        assert claim not in whole, (
            f"{fmt}: the document asserts {claim!r}. That is a verified-only "
            "denominator; _disclosure.unverified_banner adjudicates the "
            "opposite in the same document and records that a verified-only "
            "denominator OVERSTATES, in the direction that flatters the "
            "applicant."
        )


@pytest.mark.parametrize("fmt", SURFACES)
def test_the_banner_still_states_the_denominator_it_adjudicated(partial, fmt):
    """THE OTHER WAY TO 'FIX' A CONTRADICTION IS TO WEAKEN THE TRUE HALF.

    Reverting the banner to something vaguer would make the two statements
    agree and lose the disclosure. So the banner's two load-bearing phrases
    are pinned on every surface that renders it.
    """
    summary = _summary(fmt, partial[fmt])
    for anchor in BANNER_ANCHORS:
        assert anchor in summary, (
            f"{fmt}: the unverified banner no longer says {anchor!r}. The "
            "Executive Summary sentence was corrected to agree with this "
            "banner; agreeing by softening the banner is not the fix.\n\n"
            f"Read: {summary!r}"
        )


def test_the_three_surfaces_state_it_identically(partial):
    """One string, three surfaces — not three copies that agree by luck.

    ``Q25_QEI_BASIS_CLAUSE`` was three hand-typed copies in this package and
    they agreed by coincidence; editing the constant moved one surface and
    left the other three saying the old thing. The lower-bound clause is the
    same class of sentence, now sitting on three surfaces, so the rendered
    text is compared surface to surface rather than trusted.
    """
    seen = {}
    for fmt in SURFACES:
        summary = _summary(fmt, partial[fmt])
        start = summary.index(LOWER_BOUND_CLAUSE)
        seen[fmt] = summary[start:start + len(LOWER_BOUND_CLAUSE)]
    assert len(set(seen.values())) == 1, f"the clause drifted between surfaces: {seen}"


def test_no_renderer_retypes_the_clause():
    """The wording lives in _disclosure; nobody carries a second copy.

    Walks the INSTALLED package, not ``<repo>/nmtcapp`` — the sdist job runs
    from a directory with no ``nmtcapp/``, where a walk over the repo path
    would find nothing and pass. Same shape as
    ``test_headline_distress_denominator.test_the_clause_is_read_from_the_constant_not_retyped``.
    """
    import os

    import nmtcapp

    root = os.path.dirname(os.path.abspath(nmtcapp.__file__))
    fragment = "unverified projects are absent from the numerator"
    copies = []
    walked = 0
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if not name.endswith(".py") or name == "_disclosure.py":
                continue
            path = os.path.join(dirpath, name)
            walked += 1
            for lineno, line in enumerate(open(path, encoding="utf-8"), 1):
                if fragment in line and not line.lstrip().startswith("#"):
                    copies.append(f"{os.path.relpath(path, root)}:{lineno}")
    assert walked >= 40, f"walked only {walked} modules; the sweep read nothing"
    assert not copies, (
        f"the lower-bound clause is retyped at: {copies}. Read "
        "_disclosure.LOWER_BOUND_CLAUSE instead — three hand-typed copies of "
        "one sentence in this package once agreed by luck."
    )
