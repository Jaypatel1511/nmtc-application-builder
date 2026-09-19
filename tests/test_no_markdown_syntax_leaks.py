"""A section module emits format-agnostic text; markdown syntax is a leak.

THE DEFECT (1.7.1 R5). Section E's award-by-award history was built as
``f"**Award {i+1} (FY{year}):** ..."`` — markdown bold, in a content dict
that reaches four renderers. Markdown rendered it; Word and PDF printed the
asterisks, three paragraphs each, on page 14 of the published 1.7.0 PDF.

WHERE THE FIX BELONGS. The section, not the renderers. A section's content
dict is the one representation every format reads, so anything
format-specific in it is wrong for three of the four; stripping ``**`` in
Word and PDF would leave the fourth surface's formatting as the section's
concern and invite the next leak (a heading marker, a backtick, a link).
``sections/base._content_to_markdown`` is where markdown syntax is added,
and it is the markdown renderer's business. The sweep below is the reason
the choice was made on evidence: it walks every section's generated content
and asks whether any string carries markdown syntax at all.

SWEEP RECORD (2026-09-19, on a29c983): one site. ``grep`` over
``nmtcapp/sections/`` for ``**``, ``__x``, backticks, ``](http`` and
line-leading ``#`` found ``section_e_prior_awards.py:200`` and
``base.py:130`` (the latter inside ``_content_to_markdown``, which is
correct); the rendered sweep below found the same three paragraphs and
nothing else.

Two-sided: the asterisks are absent AND the award lines are present with
their figures.
"""
from __future__ import annotations

import re

import pytest

#: Markdown emphasis, code, links and headings. ``*`` alone is not matched
#: — a footnote marker or a multiplication sign is legitimate prose.
_MARKDOWN = re.compile(r"\*\*|__\w|`[^`]+`|\]\(https?://|(?:^|\n)#{1,6} ")


@pytest.fixture(scope="module")
def rendered(tmp_path_factory) -> dict:
    from nmtcapp.core.application import Application
    from tests.test_rendered_output_baseline import (
        APPLICATION_ROUND, REQUESTED_ALLOCATION, _cde, _pipeline,
    )

    app = Application(cde=_cde(), requested_allocation=REQUESTED_ALLOCATION,
                      application_round=APPLICATION_ROUND)
    app.add_pipeline(_pipeline())
    out = str(tmp_path_factory.mktemp("markdown_leak"))
    paths = app.generate(out, formats=["word", "pdf"])
    assert {"word", "pdf"} <= set(paths)
    return app, paths


def _word_strings(path: str) -> list:
    import docx
    doc = docx.Document(path)
    out = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            out.extend(cell.text for cell in row.cells)
    return out


def _pdf_text(path: str) -> str:
    from pypdf import PdfReader
    return "\n".join((page.extract_text() or "") for page in PdfReader(path).pages)


def _walk(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from _walk(k)
            yield from _walk(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _walk(v)


def test_no_section_content_carries_markdown_syntax(rendered):
    from nmtcapp.sections import ALL_SECTIONS

    app, _paths = rendered
    analysis = app.analyze()
    leaks = []
    for section in ALL_SECTIONS:
        content = section.generate_content(app, analysis)
        for text in _walk(content):
            m = _MARKDOWN.search(text)
            if m:
                leaks.append(f"{type(section).__name__}: {m.group(0)!r} in {text[:70]!r}")
    assert not leaks, (
        "section content carries markdown syntax, which three of the four "
        "renderers print literally:\n  " + "\n  ".join(leaks)
    )


def test_no_word_paragraph_carries_a_literal_double_asterisk(rendered):
    _app, paths = rendered
    hits = [s for s in _word_strings(paths["word"]) if "**" in s]
    assert not hits, f"{len(hits)} Word string(s) print '**': {hits[:3]}"


def test_no_pdf_line_carries_a_literal_double_asterisk(rendered):
    _app, paths = rendered
    hits = [ln for ln in _pdf_text(paths["pdf"]).splitlines() if "**" in ln]
    assert not hits, f"{len(hits)} PDF line(s) print '**': {hits[:3]}"


def test_the_award_lines_are_still_there(rendered):
    """Presence half: the fix removes the syntax, not the sentence."""
    app, paths = rendered
    awards = app.cde.prior_awards
    assert len(awards) >= 2, "fixture CDE has too few awards to be evidence"
    word = "\n".join(_word_strings(paths["word"]))
    pdf = _pdf_text(paths["pdf"])
    for i, award in enumerate(sorted(awards, key=lambda a: a.get("year", 0)), 1):
        label = f"Award {i} (FY{award['year']}):"
        assert label in word, f"{label!r} missing from Word"
        assert label in pdf, f"{label!r} missing from the PDF"
        assert f"${award['amount']:,.0f}" in word


def test_the_sweep_pattern_sees_the_1_7_0_leak():
    assert _MARKDOWN.search("**Award 1 (FY2019):** $40,000,000")
    assert not _MARKDOWN.search("Award 1 (FY2019): $40,000,000 — Fully Deployed.")
    assert not _MARKDOWN.search("a 2 * 3 grid, with a * footnote")
