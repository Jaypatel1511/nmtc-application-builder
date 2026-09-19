"""The first distress figure a reviewer reads states what it is a share of.

THE DEFECT (1.7.1 R8). On the full-data render, "87%" appears four times
before the block that says what it is a share of — bold, on the first page
of the Executive Summary; in the Investment Thesis; in the Pipeline
Overview; in the Deployment Strategy line — and only the fourth carries a
qualifier, which is about this tool's house band, not the denominator. The
Distress Level Commitments block labels every figure "a share of QEI, not
of QLICIs" hundreds of lines below. Question 25's commitments are
QLICI-denominated; this figure is QEI-denominated; the reader who stops at
the Executive Summary never learns that.

THE FIX carries the denominator to the FIRST occurrence — the Executive
Summary, on every surface that renders one (markdown, Word, PDF) and in
both the nominal and the partial-unverified branch — in the short form the
package already owns: ``_question_25.Q25_QEI_BASIS_CLAUSE``. Read, not
retyped, for the reason that module's own note gives: three hand-typed
copies of that clause once agreed by luck.

WHAT THIS DOES NOT DO. It does not touch the Investment Thesis, the
Pipeline Overview or the Deployment Strategy line — the scope is the first
occurrence — and it adds no attribution: the clause names no authority, so
the fund-attribution gate has nothing new to adjudicate (measured: 25
passed before and after).

Two-sided: the clause is present in the Executive Summary AND the headline
figure is still there beside it.
"""
from __future__ import annotations

import re

import pytest

from nmtcapp.renderers._question_25 import Q25_QEI_BASIS_CLAUSE


@pytest.fixture(scope="module")
def rendered(tmp_path_factory) -> tuple:
    from nmtcapp.core.application import Application
    from tests.test_rendered_output_baseline import (
        APPLICATION_ROUND, REQUESTED_ALLOCATION, _cde, _pipeline,
    )

    app = Application(cde=_cde(), requested_allocation=REQUESTED_ALLOCATION,
                      application_round=APPLICATION_ROUND)
    app.add_pipeline(_pipeline())
    out = str(tmp_path_factory.mktemp("headline"))
    paths = app.generate(out, formats=["markdown", "word", "pdf"])
    assert {"markdown", "word", "pdf"} <= set(paths)
    return app, paths


def _executive_summary(fmt: str, path: str) -> str:
    """The Executive Summary's text on one surface, and nothing after it."""
    if fmt == "markdown":
        text = open(path, encoding="utf-8").read()
        start = text.index("## Executive Summary")
        end = text.index("\n## ", start + 5)
        return text[start:end]
    if fmt == "word":
        import docx
        paras = [p.text for p in docx.Document(path).paragraphs]
        start = next(i for i, t in enumerate(paras) if t.strip() == "Executive Summary")
        end = next(i for i, t in enumerate(paras) if i > start and t.startswith("Section A"))
        return "\n".join(paras[start:end])
    from pypdf import PdfReader
    text = "\n".join((page.extract_text() or "") for page in PdfReader(path).pages)
    start = text.index("Executive Summary")
    end = text.index("Section A:", start)
    return text[start:end]


@pytest.mark.parametrize("fmt", ["markdown", "word", "pdf"])
def test_the_executive_summary_states_the_denominator(rendered, fmt):
    app, paths = rendered
    summary = _executive_summary(fmt, paths[fmt])
    share = app.analyze().pipeline_result.distress_breakdown["pct_deep_or_severe"]
    headline = f"{share:.0%} of QEI"
    assert headline in summary, f"{fmt}: the headline figure {headline!r} is not in the Executive Summary"
    # PDF extraction may break the clause across a line; compare on one line.
    flat = re.sub(r"\s+", " ", summary)
    assert Q25_QEI_BASIS_CLAUSE in flat, (
        f"{fmt}: the Executive Summary states {headline!r} without saying "
        f"what it is a share of. Expected {Q25_QEI_BASIS_CLAUSE!r} beside it."
    )
    # Beside it: within the same sentence as the headline, not somewhere later.
    i = flat.index(headline)
    sentence_end = flat.find(". ", i)
    sentence_end = len(flat) if sentence_end == -1 else sentence_end + 1
    assert Q25_QEI_BASIS_CLAUSE in flat[i:sentence_end + len(Q25_QEI_BASIS_CLAUSE) + 4], (
        f"{fmt}: the clause is in the Executive Summary but not in the "
        f"sentence that carries the headline: {flat[i:i + 200]!r}"
    )


def test_the_partial_unverified_branch_states_it_too(tmp_path):
    """The other branch that prints a headline figure carries the clause."""
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
    paths = {
        "markdown": str(tmp_path / "a.md"),
        "word": str(tmp_path / "a.docx"),
        "pdf": str(tmp_path / "a.pdf"),
    }
    MarkdownApplicationBuilder(app, analysis).save(paths["markdown"])
    WordApplicationBuilder(app, analysis).save(paths["word"])
    PDFApplicationBuilder(app, analysis).save(paths["pdf"])
    for fmt in ("markdown", "word", "pdf"):
        summary = re.sub(r"\s+", " ", _executive_summary(fmt, paths[fmt]))
        assert "unverified" in summary.lower(), f"{fmt}: fixture did not reach the partial branch"
        assert Q25_QEI_BASIS_CLAUSE in summary, f"{fmt}: partial branch lacks the clause"


def test_the_clause_is_read_from_the_constant_not_retyped():
    """No renderer carries its own copy of the clause (three once agreed by luck)."""
    import os
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "nmtcapp")
    copies = []
    for dirpath, _d, files in os.walk(root):
        for name in files:
            if not name.endswith(".py") or name == "_question_25.py":
                continue
            path = os.path.join(dirpath, name)
            for lineno, line in enumerate(open(path, encoding="utf-8"), 1):
                if Q25_QEI_BASIS_CLAUSE in line and not line.lstrip().startswith("#"):
                    copies.append(f"{os.path.relpath(path, root)}:{lineno}")
    assert not copies, f"the basis clause is retyped at: {copies}"
