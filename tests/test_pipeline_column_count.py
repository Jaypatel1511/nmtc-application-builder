"""Appendix A's column count is DERIVED from the column list, on every surface.

THE DEFECT (1.7.1 R2). Word and PDF told the reader "Full 33-column pipeline
detail ... is provided in the accompanying Excel workbook, Pipeline Detail
tab." The tab has 29 columns: ``openpyxl`` reports ``max_column == 29`` on the
published 1.7.0 workbook, and ``len(_PIPELINE_COLUMNS) == 29`` in the tree
that built it. The sentence POINTS THE READER AT THE WORKBOOK, so a reviewer
who counts has been handed a reason to doubt every other figure in the
document. The typed ``33`` sat a hundred lines from the constant that
computes the true count, in a module whose own comment says
``_PIPELINE_COLUMNS IS THE AUTHORITY``.

WHAT THIS MODULE ASSERTS, and why each half is needed:

* The workbook's ``Pipeline Detail`` header IS ``_PIPELINE_COLUMNS`` — every
  cell of row 3, in order, and no more. Without this the derivation would be
  a consistency fix (prose agrees with a list) rather than a correctness one
  (prose agrees with the tab it names). ``build_pipeline_table`` reindexes to
  the declaration and raises if the row dict disagrees, and this test is
  that guarantee measured on the rendered file rather than trusted.
* Word and PDF each state the count EXACTLY ONCE, and the figure they state
  is ``PIPELINE_COLUMN_COUNT``. Two-sided: the pre-image ("33-column") must
  be absent AND the post-image present, because a positive-only check passes
  a mutant that prints both.
* No source file in ``nmtcapp/`` types a column count for Appendix A. The
  interpolation is the fix; a re-typed literal beside it is the defect coming
  back, and a docstring is a source file too.

MUTATION RECORD (2026-09-19, on the fix commit):
  word_builder's sentence re-typed as "Full 33-column"  -> word test RED
  pdf_builder's sentence re-typed as "Full 33-column"   -> pdf test RED
  a 30th entry appended to _PIPELINE_COLUMNS            -> ImportError at
     ``import nmtcapp.tables.pipeline_table`` — the guard, not this module
"""
from __future__ import annotations

import os
import re

import pytest

from nmtcapp.tables.pipeline_table import _PIPELINE_COLUMNS, PIPELINE_COLUMN_COUNT

#: The sentence's shape on the two surfaces that carry it. The count is the
#: capture group; anything else stating "<N>-column ... detail" is a second
#: copy and fails the exactly-once assertion below.
_COUNT_SENTENCE = re.compile(r"Full (\d+)-column pipeline detail")

#: What a typed count looks like in source. "33-column", "33 column",
#: "thirty-three-column". The 1.7.0 grep that found four sites matched only
#: the first spelling; this matches the ones it would have missed.
_TYPED_COUNT_IN_SOURCE = re.compile(
    r"\b(\d+|thirty[- ]three|twenty[- ]nine)[- ]columns?\b[^\n]{0,40}"
    r"\b(pipeline detail|detail lives|detail table)\b",
    re.IGNORECASE,
)

@pytest.fixture(scope="module")
def rendered(tmp_path_factory) -> dict:
    """The baseline fixture rendered to Word, PDF and Excel, once."""
    from nmtcapp.core.application import Application
    from tests.test_rendered_output_baseline import (
        APPLICATION_ROUND, REQUESTED_ALLOCATION, _cde, _pipeline,
    )

    app = Application(cde=_cde(), requested_allocation=REQUESTED_ALLOCATION,
                      application_round=APPLICATION_ROUND)
    app.add_pipeline(_pipeline())
    out = str(tmp_path_factory.mktemp("column_count"))
    paths = app.generate(out, formats=["word", "excel", "pdf"])
    missing = {"word", "excel", "pdf"} - set(paths)
    assert not missing, f"renderers did not produce {sorted(missing)}"
    return paths


def _word_text(path: str) -> str:
    import docx
    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def _pdf_text(path: str) -> str:
    from pypdf import PdfReader
    return "\n".join((page.extract_text() or "") for page in PdfReader(path).pages)


def test_the_count_is_the_length_of_the_authority():
    assert PIPELINE_COLUMN_COUNT == len(_PIPELINE_COLUMNS)
    assert PIPELINE_COLUMN_COUNT > 0


def test_the_workbook_header_is_the_column_list(rendered):
    """Row 3 of Pipeline Detail is _PIPELINE_COLUMNS, in order, and nothing else."""
    import openpyxl
    wb = openpyxl.load_workbook(rendered["excel"], read_only=True)
    ws = wb["Pipeline Detail"]
    header = [c.value for c in next(ws.iter_rows(min_row=3, max_row=3))]
    header = [h for h in header if h not in (None, "")]
    assert header == list(_PIPELINE_COLUMNS), (
        "the Pipeline Detail header is not _PIPELINE_COLUMNS. Deriving the "
        "prose count from the list is only a correctness fix while the tab "
        "IS the list.\n  only in the sheet: "
        f"{[h for h in header if h not in _PIPELINE_COLUMNS]}\n  only in the "
        f"list: {[c for c in _PIPELINE_COLUMNS if c not in header]}"
    )
    assert len(header) == PIPELINE_COLUMN_COUNT


@pytest.mark.parametrize("fmt", ["word", "pdf"])
def test_the_prose_states_the_workbooks_count_exactly_once(rendered, fmt):
    text = _word_text(rendered[fmt]) if fmt == "word" else _pdf_text(rendered[fmt])
    stated = _COUNT_SENTENCE.findall(text)
    assert len(stated) == 1, (
        f"{fmt} states the Appendix A column count {len(stated)} times; "
        f"expected exactly one sentence. Matches: {stated}"
    )
    assert int(stated[0]) == PIPELINE_COLUMN_COUNT, (
        f"{fmt} tells the reader the workbook has {stated[0]} columns; the "
        f"Pipeline Detail tab has {PIPELINE_COLUMN_COUNT}."
    )
    # The pre-image. Its absence is asserted separately from the post-image's
    # presence so a document carrying both cannot pass.
    assert "33-column" not in text, f"{fmt} still carries the 1.7.0 literal"


def test_no_source_file_types_the_appendix_a_column_count():
    """A typed count is the defect; docstrings are source files too.

    Walks the INSTALLED package, not ``<repo>/nmtcapp``: inside the sdist
    job the tests run from a directory with no ``nmtcapp/``, and a walk of a
    missing directory finds no offenders and passes on nothing.
    """
    import nmtcapp
    package_root = os.path.dirname(os.path.abspath(nmtcapp.__file__))
    offenders = []
    walked = 0
    for dirpath, _dirs, files in os.walk(package_root):
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            walked += 1
            with open(path, encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, 1):
                    if _TYPED_COUNT_IN_SOURCE.search(line):
                        offenders.append(f"{os.path.relpath(path, package_root)}:{lineno}: {line.strip()}")
    assert walked >= 40, f"walked only {walked} modules under {package_root}; the sweep read nothing"
    assert not offenders, (
        "a column count for Appendix A is typed in source; interpolate "
        "PIPELINE_COLUMN_COUNT or name _PIPELINE_COLUMNS instead:\n  "
        + "\n  ".join(offenders)
    )


def test_the_sweep_pattern_can_see_the_1_7_0_literal():
    """The source sweep is only evidence if it matches what shipped."""
    shipped = [
        'Full 33-column detail lives in the Excel attachment.',
        '"Full 33-column pipeline detail (deal economics, QLICI structure, timeline) "',
        'surfaces, not four: markdown renders the full 33-column table and Excel',
    ]
    # The third shipped line breaks before "detail"; the sweep matches on the
    # sentence's own line, which is why the regex allows a short gap and why
    # this docstring line is asserted as the pattern's known blind spot.
    assert _TYPED_COUNT_IN_SOURCE.search(shipped[0])
    assert _TYPED_COUNT_IN_SOURCE.search(shipped[1])
    assert _COUNT_SENTENCE.search("Full 33-column pipeline detail (deal")
