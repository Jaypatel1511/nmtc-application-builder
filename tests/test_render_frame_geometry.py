"""No rendered text may fall outside the frame that is supposed to hold it.

THE DEFECT THIS GATE EXISTS FOR (1.3.0 FIX-2 B1)
================================================

``renderers/pdf_builder._content_to_flowables`` built every section key/value
table as::

    data = [["Item", "Value"]] + [[k, str(v)] for k, v in body.items()]
    tbl = Table(data)

No ``colWidths``, and bare ``str`` cells rather than ``Paragraph``. ReportLab
cannot wrap a string cell, so it sizes each column to the longest single line
and draws the table at whatever width that comes to. Measured on the baseline
fixture at ``ff49064``:

    Section D, page 9   table 686 pt against a 432 pt frame. Every row label
                        is pushed off the left edge and the caveat on
                        "QEI Less CDE Fees — $121,582,500" is cut mid-word at
                        the right. A CDE copying that figure gets the number
                        without the sentence saying what it is not.

    Section B, page 5   table 17,197 pt wide, because the ~4,000-character
                        Q25 basis note becomes one unwrappable column. The
                        page renders as a header bar and four empty striped
                        rows: 1.3.0's two reasons for existing, invisible.

753 words rendered outside the printable band, on those two pages, in a
document whose source text was correct throughout.

WHY EVERY EXISTING GATE MISSED IT
=================================

``tests/rendered_baseline/pdf.txt`` is ``page.extract_text()`` — the text
CONTENT of each page, with no positions in it. A run drawn at x = -8,292 pt
extracts identically to one drawn at x = 90. The whole class is structurally
outside that gate, exactly as row heights are structurally outside
``excel.txt``.

``tests/test_excel_geometry.py`` — the gate 1.3.0 built for precisely this
class one commit earlier — reads the workbook and nothing else. It cannot see
PDF, Word or Markdown. So the round that existed to fix "correct in the source,
wrong on the page" shipped the same defect, worse, on the surface most likely
to be printed and handed to a reviewer.

WHAT THIS GATE ASSERTS, AND WHAT IT DOES NOT
============================================

**PDF, rendered (``test_no_rendered_pdf_text_falls_outside_its_frame``).** The
shipped file is re-opened and every text-showing operation's device position is
read back, then measured against ReportLab's own font metrics. This is the
page as a CDE sees it, including text no flowable produced — the running footer
is drawn straight onto the canvas and is checked here too.

**PDF, modelled (``test_no_pdf_table_is_wider_than_its_frame``).** Every
``Table`` in the story is asked for its own width and compared to the frame it
will be placed in. Exact, no metric estimation, and it names the offending
flowable rather than the coordinates of its debris.

**Word: covered by mechanism, not by measurement.** python-docx writes no
layout; Word computes it at open time, and nothing in this repository can
render a .docx. What is asserted instead is the mechanism that makes overflow
impossible: every key/value table is created with ``autofit`` on and no
explicit column widths, so Word fits it to the text column.
``test_word_key_value_tables_are_autofit`` fails if a renderer ever pins a
width there. That is weaker than the PDF check and is written down as weaker.

**Markdown: out of scope, and not silently.** Markdown has no frame. It reflows
to whatever is reading it, so "outside the frame" has no referent and there is
nothing to assert. ``test_markdown_has_no_frame_to_fall_out_of`` records that
as a decision rather than as an omission.

**Excel: covered by tests/test_excel_geometry.py**, which measures the one
dimension a spreadsheet clips in — row height against merged span.

THE GATE'S OWN SENSITIVITY IS TESTED, TWICE.
``test_the_checker_catches_a_table_built_without_colwidths`` restores the
shipped defect and asserts red. ``test_the_checker_cannot_pass_on_a_document
_with_nothing_in_it`` asserts that an empty document fails rather than passing
by measuring nothing — the vacuity hole this package keeps re-opening.
"""
from __future__ import annotations

import pytest

pytest.importorskip("reportlab", reason="reportlab not installed")
pytest.importorskip("pypdf", reason="pypdf not installed")

from nmtcapp.renderers._frame_geometry import (
    CHROME_BAND_TOP_PTS, chrome_bounds, frame_bounds,
)

# The measurement disagrees with Excel-grade exactness by a fraction of a
# point: ReportLab rounds coordinates into the content stream at 2 decimal
# places, and a right-aligned string lands on the boundary rather than inside
# it. Half a point is under a tenth of a character at any size this package
# draws and cannot hide a clipped word.
TOLERANCE_PTS = 0.5


# ---------------------------------------------------------------------------
# The rendered-artifact checker
# ---------------------------------------------------------------------------

def _compose(m1, m2):
    """Compose two PDF 3x2 matrices: ``m1`` applied, then ``m2``.

    pypdf hands the visitor the text matrix and the CTM separately. Reading
    ``tm[4]`` alone puts every glyph at x = 0 and reports an entire correct
    document as off-page; this is the multiplication that was missing.
    """
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (
        a1 * a2 + b1 * c2, a1 * b2 + b1 * d2,
        c1 * a2 + d1 * c2, c1 * b2 + d1 * d2,
        e1 * a2 + f1 * c2 + e2, e1 * b2 + f1 * d2 + f2,
    )


def _base_font(font_dict) -> str:
    """The Type-1 name ReportLab has metrics for, from a page's font resource."""
    from reportlab.pdfbase import pdfmetrics
    if not font_dict:
        return "Helvetica"
    raw = font_dict.get("/BaseFont")
    if raw is None:
        return "Helvetica"
    name = str(raw).lstrip("/")
    if "+" in name:                       # strip a subset tag
        name = name.split("+", 1)[1]
    try:
        pdfmetrics.getFont(name)
    except Exception:
        return "Helvetica"
    return name


def check_pdf_frames(path: str) -> tuple:
    """Return ``(findings, words_measured)`` for a rendered PDF.

    A finding is one text run whose drawn extent crosses the left or right
    edge of the band it was drawn in. Two bands exist, told apart by height:
    below :data:`CHROME_BAND_TOP_PTS` is the running header/footer, which is
    drawn straight onto the canvas at its own margin; above it is the body
    frame, which is what flowables are laid into.

    Example::

        findings, measured = check_pdf_frames("application.pdf")
        assert not findings and measured > 0
    """
    from pypdf import PdfReader
    from reportlab.pdfbase import pdfmetrics

    findings = []
    measured = 0
    for index, page in enumerate(PdfReader(path).pages, start=1):
        page_w = float(page.mediabox.width)
        page_h = float(page.mediabox.height)
        landscape = page_w > page_h
        runs = []

        def visitor(text, cm, tm, font_dict, font_size, _runs=runs):
            if not text or not text.strip():
                return
            _runs.append((_compose(tm, cm), _base_font(font_dict), font_size, text))

        page.extract_text(visitor_text=visitor)

        for matrix, font, size, text in runs:
            x, y, x_scale = matrix[4], matrix[5], abs(matrix[0]) or 1.0
            words = text.split()
            if not words:
                continue
            measured += len(words)
            try:
                size = float(size)
            except (TypeError, ValueError):
                size = 9.0
            # pypdf appends a newline to each extracted run. It is not a drawn
            # glyph, and ReportLab charges it ~0.75 of the point size, which is
            # enough to manufacture an overflow out of a right-aligned footer.
            drawn = text.strip("\r\n")
            width = pdfmetrics.stringWidth(drawn, font, size) * x_scale
            left, right = (
                chrome_bounds(page_w, landscape=landscape)
                if y < CHROME_BAND_TOP_PTS
                else frame_bounds(page_w, landscape=landscape)
            )
            if x < left - TOLERANCE_PTS or x + width > right + TOLERANCE_PTS:
                findings.append(
                    f"page {index}: {len(words)} word(s) drawn from x={x:.1f} to "
                    f"x={x + width:.1f} pt, outside the {left:.0f}–{right:.0f} pt "
                    f"frame. The reader sees the part inside and nothing else. "
                    f"{drawn[:80]!r}"
                )
    return findings, measured


# ---------------------------------------------------------------------------
# The modelled checker
# ---------------------------------------------------------------------------

def check_story_widths(story, *, portrait_avail: float, landscape_avail: float) -> tuple:
    """Return ``(findings, tables_measured)`` for a ReportLab story.

    Walks the story tracking which page template is in force — the story
    switches to landscape for Appendix B and back — and asks every ``Table``
    for the width it will draw at against that template's frame.

    Example::

        findings, n = check_story_widths(story, portrait_avail=432.0,
                                         landscape_avail=684.0)
    """
    from reportlab.platypus import NextPageTemplate, Table

    findings = []
    measured = 0
    avail = portrait_avail
    for item in story:
        if isinstance(item, NextPageTemplate):
            # ('nextPageTemplate', <name>) — the flowable keeps the template
            # name only inside its action tuple.
            name = item.action[1]
            name = name[0] if isinstance(name, (list, tuple)) else name
            avail = landscape_avail if name == "Landscape" else portrait_avail
            continue
        if not isinstance(item, Table):
            continue
        measured += 1
        width = item.wrap(avail, 10_000)[0]
        if width > avail + TOLERANCE_PTS:
            first_row = " | ".join(
                getattr(c, "text", str(c))[:40] for c in (item._cellvalues[0] if item._cellvalues else [])
            )
            findings.append(
                f"a {len(item._cellvalues)}-row table draws {width:.0f} pt wide "
                f"into a {avail:.0f} pt frame — {width - avail:.0f} pt of it is "
                f"off the page. First row: {first_row!r}"
            )
    return findings, measured


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def rendered_pdf(tmp_path_factory):
    """The baseline fixture, rendered — the same document the baseline gate diffs."""
    from nmtcapp.core.application import Application
    from nmtcapp.renderers.pdf_builder import PDFApplicationBuilder
    from tests.test_rendered_output_baseline import (
        APPLICATION_ROUND, REQUESTED_ALLOCATION, _cde, _pipeline,
    )

    app = Application(cde=_cde(), requested_allocation=REQUESTED_ALLOCATION,
                      application_round=APPLICATION_ROUND)
    app.add_pipeline(_pipeline())
    path = str(tmp_path_factory.mktemp("frames") / "application.pdf")
    PDFApplicationBuilder(app, app.analyze()).save(path)
    return path


@pytest.fixture(scope="module")
def rendered_pdf_builder():
    """The same document as a builder and its styles, for the modelled check."""
    from nmtcapp.core.application import Application
    from nmtcapp.renderers.pdf_builder import PDFApplicationBuilder, _build_styles
    from tests.test_rendered_output_baseline import (
        APPLICATION_ROUND, REQUESTED_ALLOCATION, _cde, _pipeline,
    )

    app = Application(cde=_cde(), requested_allocation=REQUESTED_ALLOCATION,
                      application_round=APPLICATION_ROUND)
    app.add_pipeline(_pipeline())
    return PDFApplicationBuilder(app, app.analyze()), _build_styles()


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------

def test_no_rendered_pdf_text_falls_outside_its_frame(rendered_pdf):
    """Read the shipped page back and measure where the ink actually landed."""
    findings, measured = check_pdf_frames(rendered_pdf)
    assert measured > 0, (
        "no text was measured at all. The document rendered nothing, or the "
        "extraction stopped working — either way this gate just passed on a "
        "blank page, which is the vacuity it exists to refuse."
    )
    assert not findings, (
        f"{len(findings)} text run(s) render outside their frame, out of "
        f"{measured} words measured. This is 1.3.0 FIX-2 B1's class: text that "
        "is correct in the source and off the page. tests/rendered_baseline/"
        "pdf.txt cannot see it — extract_text() carries no positions.\n\n"
        + "\n\n".join(findings)
    )


def test_no_pdf_table_is_wider_than_its_frame(rendered_pdf_builder):
    """The same defect, named at its source rather than at its debris.

    ``check_pdf_frames`` reports coordinates; this reports the table. Both are
    kept because they fail on different things: a table can be the right width
    and still push a right-aligned run past the edge, and a run can land inside
    the frame on a table that is wider than it (ReportLab centres the overflow).
    """
    from nmtcapp.renderers._frame_geometry import usable_width

    builder, styles = rendered_pdf_builder
    findings, measured = check_story_widths(
        builder._build_story(styles),
        portrait_avail=usable_width(),
        landscape_avail=usable_width(landscape=True),
    )
    assert measured > 0, (
        "the story contained no tables at all. Either the document stopped "
        "rendering its tables or the walk stopped finding them; this gate "
        "must not pass by measuring nothing."
    )
    assert not findings, (
        f"{len(findings)} of {measured} tables draw wider than their frame:\n\n"
        + "\n\n".join(findings)
    )


def test_the_checker_catches_a_table_built_without_colwidths(rendered_pdf_builder):
    """Restore ``Table(data)`` and prove the checker goes red on it.

    A gate that has never been seen to fail is a gate nobody has evidence
    about. This is the shipped 1.3.0 call site, rebuilt: bare ``str`` cells,
    no ``colWidths``, on the real Section B content — the ~4,000-character
    Q25 basis note that rendered as four empty striped rows.
    """
    from reportlab.platypus import Table
    from nmtcapp.renderers._frame_geometry import usable_width
    from nmtcapp.sections import ALL_SECTIONS

    from nmtcapp.renderers._question_25 import Q25_BASIS_LABEL

    builder, _ = rendered_pdf_builder
    # Section B's, named by the key it carries rather than by position: the
    # first dict table_ref in ALL_SECTIONS is Section A's pipeline overview,
    # which is short enough to fit and would have made this test pass on a
    # defect it never reproduced.
    body = next(
        sub["body"]
        for gen in ALL_SECTIONS
        for sub in gen.generate_content(builder.application, builder.analysis)["subsections"]
        if sub.get("type") == "table_ref" and isinstance(sub.get("body"), dict)
        and Q25_BASIS_LABEL in sub["body"]
    )
    defect = Table([["Item", "Value"]] + [[k, str(v)] for k, v in body.items()])

    findings, measured = check_story_widths(
        [defect], portrait_avail=usable_width(), landscape_avail=usable_width(landscape=True),
    )
    assert measured == 1
    assert findings, (
        "the checker did not flag a colWidths-less table of the real Section B "
        "content — it cannot catch the defect it exists for"
    )
    assert "off the page" in findings[0], findings


def test_the_checker_cannot_pass_on_a_document_with_nothing_in_it(tmp_path):
    """An empty PDF must FAIL this gate, not pass it.

    ``assert not findings`` is true of a blank page, of a page whose text
    extraction broke, and of a document that never rendered. Three of this
    package's gates have shipped in that shape. The ``measured > 0`` assertion
    in the gate above is what refuses it, and this is the test that the
    refusal works.
    """
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import LETTER

    path = str(tmp_path / "blank.pdf")
    c = rl_canvas.Canvas(path, pagesize=LETTER)
    c.showPage()
    c.save()

    findings, measured = check_pdf_frames(path)
    assert findings == [] and measured == 0
    with pytest.raises(AssertionError, match="vacuity"):
        test_no_rendered_pdf_text_falls_outside_its_frame(path)


# ---------------------------------------------------------------------------
# The other three surfaces, ruled explicitly
# ---------------------------------------------------------------------------

def test_word_key_value_tables_are_autofit(sample_application, application_analysis, tmp_path):
    """Word cannot overflow here because nothing pins a width — asserted, not assumed.

    This is the mechanism, not a measurement. Nothing in this repository can
    lay out a .docx, so the claim "Word carries the basis note correctly" rests
    on ``add_styled_table`` creating the table with ``autofit`` on and passing
    no ``col_widths`` for the ``table_ref`` path. If a renderer ever pins a
    width on a key/value table, Word gets PDF's defect and this fails.
    """
    from docx import Document
    from docx.shared import Emu
    from nmtcapp.renderers.word_builder import WordApplicationBuilder

    path = str(tmp_path / "application.docx")
    WordApplicationBuilder(sample_application, application_analysis).save(path)

    doc = Document(path)
    # The widest text column in the document: a table can sit in any section,
    # and the landscape appendices are wider than the portrait body.
    text_width = Emu(max(
        s.page_width - s.left_margin - s.right_margin for s in doc.sections
    ))
    overwide = []
    for i, table in enumerate(doc.tables):
        widths = [c.width for c in table.columns if c.width is not None]
        if widths and Emu(sum(int(w) for w in widths)) > text_width:
            overwide.append(
                f"table {i} ({len(table.columns)} columns) pins "
                f"{Emu(sum(int(w) for w in widths)).inches:.2f} in of column width "
                f"into a {text_width.inches:.2f} in text column"
            )
    assert not overwide, (
        "a Word table pins column widths past the page's text column. Word "
        "will not reflow past a pinned width, so this is PDF's B1 arriving on "
        "the .docx surface.\n" + "\n".join(overwide)
    )


def test_markdown_has_no_frame_to_fall_out_of(sample_application, application_analysis):
    """Recorded as a decision, so the omission cannot read as coverage.

    Markdown carries no page, no margin and no column width; it reflows to
    whatever renders it. "Outside the frame" has no referent, so there is
    nothing here to assert and no gate to write. What IS asserted is that
    Markdown still carries the content whose PDF rendering was the defect —
    if it ever stops, that is a different gate's failure and this one says so.
    """
    from nmtcapp.renderers.markdown_builder import MarkdownApplicationBuilder
    from nmtcapp.renderers._question_25 import Q25_BASIS_LABEL

    md = MarkdownApplicationBuilder(sample_application, application_analysis).build()
    assert Q25_BASIS_LABEL in md, (
        "the Q25 basis note is not in the Markdown output. Markdown cannot "
        "clip it — but it can drop it, and that is what this line watches."
    )
