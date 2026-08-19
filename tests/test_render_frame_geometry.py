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

BOTH GATES CARRY BOTH PROOFS. 1.3.0 SHIPPED THEM CROSSED (1.3.1 G2).
A gate needs two independent proofs and they answer different questions:

    SENSITIVITY  does it go RED on the defect it exists for?
    VACUITY      does it REFUSE to go green on a document with nothing in it?

Through 1.3.0 the RENDERED checker had only the vacuity proof and the MODELLED
checker had only the sensitivity proof, and this docstring said "tested, twice"
— which was true of the pair and false of either one. Each now has both:

    rendered   sensitivity  ..._catches_a_rendered_table_built_without_colwidths
               vacuity      ..._cannot_pass_on_a_document_with_nothing_in_it
    modelled   sensitivity  ..._catches_a_table_built_without_colwidths
               vacuity      ..._cannot_pass_on_a_story_with_no_tables_in_it

THREE FAILURE MODES, AND WHICH GATE CATCHES WHICH (1.3.1 G2)
============================================================

``Table(data)`` can be wrong in three distinct ways and they do not all reach
the same gate. ``test_the_three_table_failure_modes_reach_the_gates_they_reach``
executes all three and pins the matrix:

    1. NO ``colWidths``, bare ``str`` cells — the shipped B1 defect. ReportLab
       sizes columns to the longest unwrapped line and draws the table at
       whatever that comes to. BOTH gates catch it: modelled at 17,197 pt
       against a 432 pt frame, rendered at x = -8,293 pt.
    2. NO ``colWidths``, ``Paragraph`` cells. The paragraphs wrap, but
       ReportLab still splits the available width evenly rather than by
       content, so nothing overflows. NEITHER gate fires, and neither should.
    3. ``colWidths`` set, a cell taller than the frame, no ``splitInRow=1``.
       ReportLab raises ``LayoutError`` at build time rather than overflowing.
       NEITHER gate sees it — the build never produces a story to walk or a
       file to read. It is caught by the render itself, and that is written
       down here so "the frame gates are green" is never read as "the table
       renders".
"""
from __future__ import annotations

import pytest

pytest.importorskip("reportlab", reason="reportlab not installed")
pytest.importorskip("pypdf", reason="pypdf not installed")

from nmtcapp.renderers._frame_geometry import (
    CHROME_BAND_TOP_PTS, CHROME_TEXT_BASELINES_PTS, chrome_bounds,
    frame_bounds, is_chrome_baseline,
)

# The measurement disagrees with Excel-grade exactness by a fraction of a
# point: ReportLab rounds coordinates into the content stream at 2 decimal
# places, and a right-aligned string lands on the boundary rather than inside
# it. Half a point is under a tenth of a character at any size this package
# draws and cannot hide a clipped word.
TOLERANCE_PTS = 0.5


# ---------------------------------------------------------------------------
# The rendered-artifact checker
#
# WHY THIS READS THE CONTENT STREAM AND NOT ``extract_text(visitor_text=...)``
# ============================================================================
#
# 1.3.0's version of this checker asked pypdf's text-extraction visitor for
# each run's matrix and font, then measured the run with
# ``pdfmetrics.stringWidth`` on the DECODED text. It reported one false
# positive on ordinary input — a 45- and a 50-project pipeline, page 5, the
# aggregate-impact bullet list — and reproducing it (1.3.1 G3) found two
# independent faults, neither of them the one that had been supposed:
#
# THE WIDTH WAS MEASURED THROUGH A UNICODE ROUND TRIP THAT DOES NOT CLOSE.
#     ReportLab's WinAnsiEncoding table puts ``bullet`` at code 0x7F, where the
#     PDF specification's table leaves the code unused. So ReportLab DRAWS a
#     bullet as byte 0x7F; pypdf DECODES byte 0x7F to U+007F (DEL); and
#     ``pdfmetrics.stringWidth`` cannot encode U+007F in winansi at all and
#     falls back to 0.761 em where the bullet it actually drew is 0.350 em.
#     Every bullet on a line inflated the measurement by 4.5 pt at 11 pt. The
#     line that "overflowed" measures 420.00 pt exactly — the frame's inner
#     width to the hundredth — and was reported at 434.15 because it carried
#     three bullets. THE THRESHOLD WAS NEVER THE PROBLEM AND WIDENING IT WOULD
#     HAVE TURNED THIS GATE INTO A COMMENT.
#
# THE Y COORDINATE WAS NOT A COORDINATE.
#     pypdf's visitor reports a text matrix whose translation it advances by
#     the LEADING TIMES THE FONT SIZE rather than by the leading, so the second
#     line of a paragraph came back 165 pt below the first instead of 15. Runs
#     deep in a wrapped block arrived at y = -1,109 on a page where they are
#     drawn at y = 77. Since the band is chosen by height, every one of them
#     was measured against the CHROME band — 18 pt wider each side than the
#     body frame they are actually laid into. The gate was false-positiving and
#     under-checking at the same time, and only the first was visible.
#
# So the runs are taken from the content stream directly: one entry per
# text-showing operator, positioned by the PDF's own text-state machine, and
# measured from the RAW BYTES against the font's code-indexed widths. No
# decode, no re-encode, no estimate. On the shipped document every measurement
# lands on an exact hundredth — "Page N" ends at 540.00 pt, the chrome band's
# right edge, and the bullet line at 516.00, the body frame's.
# ---------------------------------------------------------------------------

_IDENTITY = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def _compose(m1, m2):
    """Compose two PDF 3x2 matrices: ``m1`` applied, then ``m2``."""
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (
        a1 * a2 + b1 * c2, a1 * b2 + b1 * d2,
        c1 * a2 + d1 * c2, c1 * b2 + d1 * d2,
        e1 * a2 + f1 * c2 + e2, e1 * b2 + f1 * d2 + f2,
    )


def _code_widths(font_obj) -> list:
    """Glyph widths per 1000 units, indexed by BYTE CODE, for a page font.

    The PDF's own ``/Widths`` array when it carries one; otherwise ReportLab's
    metrics for the base-14 font, which is the table ReportLab drew with and
    is therefore the authority for what is on the page. Indexed by code, never
    by unicode character — see this section's header for why that distinction
    is the whole of G3.
    """
    from reportlab.pdfbase import pdfmetrics

    widths = [0.0] * 256
    first, arr = font_obj.get("/FirstChar"), font_obj.get("/Widths")
    if arr is not None and first is not None:
        first = int(first)
        for i, w in enumerate(arr.get_object()):
            if 0 <= first + i < 256:
                widths[first + i] = float(w)
        return widths

    name = str(font_obj.get("/BaseFont", "/Helvetica")).lstrip("/")
    if "+" in name:                       # strip a subset tag
        name = name.split("+", 1)[1]
    try:
        font = pdfmetrics.getFont(name)
    except Exception:
        font = pdfmetrics.getFont("Helvetica")
    for i in range(256):
        try:
            widths[i] = float(font.widths[i])
        except Exception:
            widths[i] = 0.0
    return widths


def _raw_bytes(operand) -> bytes:
    """The bytes a text-showing operand puts on the page, never its decode."""
    raw = getattr(operand, "original_bytes", None)
    if raw is not None:
        return bytes(raw)
    if isinstance(operand, bytes):
        return operand
    return str(operand).encode("latin-1", "replace")


def positioned_runs(page) -> list:
    """Every text-showing operation on ``page``, with its device geometry.

    Returns a list of ``{"x", "y", "width", "raw", "font", "size"}`` in draw
    order. ``x``/``y`` are the run's origin on the page in points and ``width``
    is its drawn extent — both exact, both from the PDF's own text-state
    machine rather than from a text extractor's reconstruction of it.

    Example::

        runs = positioned_runs(PdfReader("application.pdf").pages[4])
        max(r["x"] + r["width"] for r in runs)      # -> 540.0
    """
    from pypdf.generic import ContentStream

    resources = page.get("/Resources") or {}
    fonts = resources.get("/Font") or {}
    width_cache = {}

    ctm, ctm_stack = _IDENTITY, []
    tm = tlm = _IDENTITY
    font_key, size = None, 0.0
    leading = char_space = word_space = rise = 0.0
    h_scale = 1.0
    runs = []

    def show(raw: bytes) -> None:
        nonlocal tm
        if font_key not in fonts:
            return
        if font_key not in width_cache:
            width_cache[font_key] = _code_widths(fonts[font_key].get_object())
        widths = width_cache[font_key]
        advance = 0.0
        for code in raw:
            advance += (widths[code] / 1000.0 * size + char_space
                        + (word_space if code == 32 else 0.0)) * h_scale
        placed = _compose(_compose((size * h_scale, 0.0, 0.0, size, 0.0, rise),
                                   tm), ctm)
        device = _compose(tm, ctm)
        runs.append({
            "x": placed[4], "y": placed[5],
            "width": advance * (abs(device[0]) or 1.0),
            "raw": raw, "font": font_key, "size": size,
        })
        tm = _compose((1.0, 0.0, 0.0, 1.0, advance, 0.0), tm)

    def next_line() -> None:
        nonlocal tm, tlm
        tlm = _compose((1.0, 0.0, 0.0, 1.0, 0.0, -leading), tlm)
        tm = tlm

    for operands, operator in ContentStream(page.get_contents(), getattr(page, "pdf", None)).operations:
        op = operator.decode("latin-1") if isinstance(operator, bytes) else operator
        if op == "q":
            ctm_stack.append(ctm)
        elif op == "Q":
            if ctm_stack:
                ctm = ctm_stack.pop()
        elif op == "cm":
            ctm = _compose(tuple(float(v) for v in operands), ctm)
        elif op == "BT":
            tm = tlm = _IDENTITY
        elif op == "Tf":
            font_key, size = str(operands[0]), float(operands[1])
        elif op == "TL":
            leading = float(operands[0])
        elif op == "Tc":
            char_space = float(operands[0])
        elif op == "Tw":
            word_space = float(operands[0])
        elif op == "Tz":
            h_scale = float(operands[0]) / 100.0
        elif op == "Ts":
            rise = float(operands[0])
        elif op == "Tm":
            tm = tlm = tuple(float(v) for v in operands)
        elif op in ("Td", "TD"):
            if op == "TD":
                leading = -float(operands[1])
            tlm = _compose((1.0, 0.0, 0.0, 1.0, float(operands[0]),
                            float(operands[1])), tlm)
            tm = tlm
        elif op == "T*":
            next_line()
        elif op == "Tj":
            show(_raw_bytes(operands[0]))
        elif op == "'":
            next_line()
            show(_raw_bytes(operands[0]))
        elif op == '"':
            word_space, char_space = float(operands[0]), float(operands[1])
            next_line()
            show(_raw_bytes(operands[2]))
        elif op == "TJ":
            for element in operands[0]:
                if isinstance(element, (int, float)):
                    tm = _compose((1.0, 0.0, 0.0, 1.0,
                                   -float(element) / 1000.0 * size * h_scale,
                                   0.0), tm)
                else:
                    show(_raw_bytes(element))
    return runs


def check_pdf_frames(path: str) -> tuple:
    """Return ``(findings, words_measured)`` for a rendered PDF.

    A finding is one text run whose drawn extent crosses the left or right
    edge of the band it was drawn in. Two bands exist: the running footer,
    which is drawn straight onto the canvas at its own margin, and the body
    frame, which is what flowables are laid into.

    THE FOOTER BAND IS A BOUND, NOT A SKIP (1.3.1 G6). It is 18 pt wider each
    side than the body frame, so which runs get it decides what this gate can
    see. Before 1.3.1 any run below :data:`CHROME_BAND_TOP_PTS` got it — which
    is a height test, and a height test hands the slack to a body flowable that
    lands low on the page as readily as to a page number. It is now granted
    only to runs drawn AT a height the footer actually draws at
    (:data:`CHROME_TEXT_BASELINES_PTS`). Everything else on the page is
    measured against the body frame, including anything below it.

    Example::

        findings, measured = check_pdf_frames("application.pdf")
        assert not findings and measured > 0
    """
    from pypdf import PdfReader

    findings = []
    measured = 0
    for index, page in enumerate(PdfReader(path).pages, start=1):
        page_w = float(page.mediabox.width)
        page_h = float(page.mediabox.height)
        landscape = page_w > page_h

        for run in positioned_runs(page):
            raw = run["raw"]
            if not raw.strip():
                continue
            measured += len(raw.split())
            chrome = is_chrome_baseline(run["y"])
            left, right = (chrome_bounds if chrome else frame_bounds)(
                page_w, landscape=landscape)
            x, end = run["x"], run["x"] + run["width"]
            if x < left - TOLERANCE_PTS or end > right + TOLERANCE_PTS:
                findings.append(
                    f"page {index}: {len(raw.split())} word(s) drawn from "
                    f"x={x:.1f} to x={end:.1f} pt at y={run['y']:.1f}, outside "
                    f"the {left:.0f}\u2013{right:.0f} pt "
                    f"{'footer' if chrome else 'body'} frame. The reader sees "
                    f"the part inside and nothing else. "
                    f"{raw.decode('latin-1')[:80]!r}"
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
#
# THREE STATES, NOT ONE (1.3.1 G4). ``tests/test_excel_geometry`` parametrises
# over ``STATES`` because BOTH of 1.3.0's banner defects lived in the two
# states its first version never built. This gate rendered the baseline
# document and nothing else, which is the same eye shut on the surface most
# likely to be printed. It now builds the same three.
#
# WHAT THE PARAMETRISATION STILL DOES NOT COVER, stated so the coverage cannot
# be read as more than it is:
#
#   PIPELINE SIZE. One pipeline, eight projects. The G3 false positive
#     appeared at 45 and 50 and not at 20, because the wrap point moves with
#     the digit count of an aggregate. Nothing here renders a large pipeline;
#     ``test_the_measurement_holds_at_pipeline_sizes_that_move_the_wrap`` is
#     the answer to exactly that and covers 20/45/50 on the nominal state only.
#   CDE-SUPPLIED TEXT. Every string a CDE types — mission, contact, project
#     and QALICB names — comes from one fixture. A 400-character project name
#     is not rendered by anything in this file.
#   PAGE SIZE AND FONT. US Letter, Helvetica, base-14, WinAnsi. A CJK or
#     TrueType face would take the ``/Widths`` arm of ``_code_widths``, which
#     nothing here exercises.
#   THE COVER PAGE'S OWN FRAME. Checked as part of the document, but no proof
#     exists that a cover-page overflow would be caught rather than absorbed
#     by the cover frame's wider margins.
# ---------------------------------------------------------------------------

STATES = ("nominal", "partial_unverified", "degraded")


def _baseline_application():
    """The baseline fixture as an Application — the document the baseline gate diffs."""
    from nmtcapp.core.application import Application
    from tests.test_rendered_output_baseline import (
        APPLICATION_ROUND, REQUESTED_ALLOCATION, _cde, _pipeline,
    )

    app = Application(cde=_cde(), requested_allocation=REQUESTED_ALLOCATION,
                      application_round=APPLICATION_ROUND)
    app.add_pipeline(_pipeline())
    return app


@pytest.fixture(scope="module", params=STATES)
def rendered_pdf(request, tmp_path_factory):
    """The baseline document rendered in each of the three analyzer states."""
    from nmtcapp.renderers.pdf_builder import PDFApplicationBuilder
    from tests.test_excel_geometry import _analysis_in_state

    app = _baseline_application()
    analysis = _analysis_in_state(app.analyze(), request.param)
    path = str(tmp_path_factory.mktemp(f"frames_{request.param}") / "application.pdf")
    PDFApplicationBuilder(app, analysis).save(path)
    return path


@pytest.fixture(scope="module", params=STATES)
def rendered_pdf_builder(request):
    """The same document as a builder and its styles, for the modelled check."""
    from nmtcapp.renderers.pdf_builder import PDFApplicationBuilder, _build_styles
    from tests.test_excel_geometry import _analysis_in_state

    app = _baseline_application()
    analysis = _analysis_in_state(app.analyze(), request.param)
    return PDFApplicationBuilder(app, analysis), _build_styles()


def _section_b_body(builder):
    """Section B's key/value body — the ~4,000-character Q25 basis note.

    Named by the key it carries rather than by position: the first dict
    ``table_ref`` in ``ALL_SECTIONS`` is Section A's pipeline overview, which
    is short enough to fit and would make a sensitivity proof pass on a defect
    it never reproduced.
    """
    from nmtcapp.sections import ALL_SECTIONS
    from nmtcapp.renderers._question_25 import Q25_BASIS_LABEL

    return next(
        sub["body"]
        for gen in ALL_SECTIONS
        for sub in gen.generate_content(builder.application, builder.analysis)["subsections"]
        if sub.get("type") == "table_ref" and isinstance(sub.get("body"), dict)
        and Q25_BASIS_LABEL in sub["body"]
    )


def _render_story(story, path):
    """Build a one-off PDF from a story, into the same frame the builder uses."""
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate
    from nmtcapp.renderers._frame_geometry import (
        BODY_MARGIN_INCHES, FRAME_BOTTOM_INCHES,
    )

    margin = BODY_MARGIN_INCHES * inch
    SimpleDocTemplate(
        path, pagesize=LETTER, leftMargin=margin, rightMargin=margin,
        topMargin=margin, bottomMargin=FRAME_BOTTOM_INCHES * inch,
    ).build(story)
    return path


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


# ---------------------------------------------------------------------------
# The modelled checker's two proofs
# ---------------------------------------------------------------------------

def test_the_checker_catches_a_table_built_without_colwidths(rendered_pdf_builder):
    """SENSITIVITY, modelled. Restore ``Table(data)`` and prove it goes red.

    A gate that has never been seen to fail is a gate nobody has evidence
    about. This is the shipped 1.3.0 call site, rebuilt: bare ``str`` cells,
    no ``colWidths``, on the real Section B content — the ~4,000-character
    Q25 basis note that rendered as four empty striped rows.
    """
    from reportlab.platypus import Table
    from nmtcapp.renderers._frame_geometry import usable_width

    builder, _ = rendered_pdf_builder
    body = _section_b_body(builder)
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


def test_the_checker_cannot_pass_on_a_story_with_no_tables_in_it():
    """VACUITY, modelled. A story with nothing to measure must ERROR, not pass.

    ADDED IN 1.3.1 (G2). Through 1.3.0 the modelled gate carried a
    ``measured > 0`` assertion and no proof that it fires, which is the same
    shape as an untested exception handler. Three documents are tried, in
    increasing order of emptiness: a story with flowables but no tables, an
    empty story, and — the one that matters — a document from which the
    ``table_ref`` section was removed entirely, which is what a renderer
    regression actually looks like.
    """
    from reportlab.platypus import Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from nmtcapp.renderers._frame_geometry import usable_width

    style = getSampleStyleSheet()["BodyText"]
    for label, story in (
        ("no tables", [Paragraph("Section B: Community Outcomes", style), Spacer(1, 12)]),
        ("no flowables", []),
    ):
        findings, measured = check_story_widths(
            story, portrait_avail=usable_width(),
            landscape_avail=usable_width(landscape=True),
        )
        assert (findings, measured) == ([], 0), label
        with pytest.raises(AssertionError, match="measuring nothing"):
            test_no_pdf_table_is_wider_than_its_frame((_StoryOnly(story), None))


class _StoryOnly:
    """A stand-in builder whose story is fixed, for the vacuity proof above."""

    def __init__(self, story):
        self._story = story

    def _build_story(self, _styles):
        return self._story


# ---------------------------------------------------------------------------
# The rendered checker's two proofs
# ---------------------------------------------------------------------------

def test_the_checker_catches_a_rendered_table_built_without_colwidths(rendered_pdf_builder, tmp_path):
    """SENSITIVITY, rendered. The same defect, actually put on a page.

    ADDED IN 1.3.1 (G2). Through 1.3.0 the rendered checker had only a vacuity
    proof, so nothing established that it goes red on ink outside the frame —
    only that it refuses a blank page. This renders the real B1 defect and
    measures the file, which is the whole of what this gate claims to do.

    The coordinate is the evidence: ReportLab centres the over-wide table, so
    the row labels land at x = -8,293 pt on a 612 pt page. That number is the
    one this module's header records from the shipped 1.3.0 artifact.
    """
    from reportlab.platypus import Table

    builder, _ = rendered_pdf_builder
    body = _section_b_body(builder)
    defect = Table([["Item", "Value"]] + [[k, str(v)] for k, v in body.items()])
    path = _render_story([defect], str(tmp_path / "defect.pdf"))

    findings, measured = check_pdf_frames(path)
    assert measured > 0, "the defect document rendered no text to measure"
    assert findings, (
        "the rendered checker did not flag a colWidths-less table of the real "
        "Section B content, drawn onto an actual page. It cannot see the "
        "defect it exists for."
    )
    assert any("x=-8" in f for f in findings), (
        "the defect rendered, but not off the left edge — the reproduction "
        "has drifted from the shipped 1.3.0 artifact and the proof no longer "
        f"proves what it says:\n" + "\n".join(findings[:3])
    )


def test_the_checker_cannot_pass_on_a_document_with_nothing_in_it(tmp_path):
    """VACUITY, rendered. An empty PDF must FAIL this gate, not pass it.

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
# Neither gate passes on the other's defect, and the third mode reaches neither
# ---------------------------------------------------------------------------

def test_the_three_table_failure_modes_reach_the_gates_they_reach(rendered_pdf_builder, tmp_path):
    """Pin the matrix in this module's header by executing all three modes."""
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, Table
    from nmtcapp.renderers._frame_geometry import usable_width

    builder, _ = rendered_pdf_builder
    body = _section_b_body(builder)
    style = getSampleStyleSheet()["BodyText"]
    avail = usable_width()

    def modelled(story):
        findings, _ = check_story_widths(story, portrait_avail=avail,
                                         landscape_avail=usable_width(landscape=True))
        return bool(findings)

    # MODE 1 — no colWidths, bare str cells. Both gates.
    mode1 = Table([["Item", "Value"]] + [[k, str(v)] for k, v in body.items()])
    assert modelled([mode1]), "mode 1 escaped the modelled gate"
    findings, _ = check_pdf_frames(_render_story([mode1], str(tmp_path / "m1.pdf")))
    assert findings, "mode 1 escaped the rendered gate"

    # MODE 2 — no colWidths, Paragraph cells. Neither gate, and neither should:
    # ReportLab splits the available width between wrapping columns and nothing
    # leaves the frame.
    mode2 = Table([[Paragraph("Item", style), Paragraph("Value", style)]]
                  + [[Paragraph(str(k), style), Paragraph(str(v), style)]
                     for k, v in body.items()])
    assert not modelled([mode2]), (
        "mode 2 was flagged. Paragraph cells wrap; if this fires, the modelled "
        "checker is measuring something other than the drawn width and would "
        "report a correct document."
    )

    # MODE 3 — colWidths set, a row taller than the frame, no splitInRow. The
    # build RAISES; there is no story to walk and no file to read, so neither
    # gate sees it and the render is what catches it.
    tall = Table([[Paragraph(str(k), style), Paragraph(str(v), style)]
                  for k, v in body.items()],
                 colWidths=[avail * 0.4, avail * 0.6])
    assert not modelled([tall]), "mode 3's story walk should find nothing over-wide"
    with pytest.raises(Exception) as excinfo:
        _render_story([tall], str(tmp_path / "m3.pdf"))
    assert "too large" in str(excinfo.value).lower() or "LayoutError" in type(excinfo.value).__name__, (
        f"mode 3 did not raise the hard layout error this matrix records; it "
        f"raised {type(excinfo.value).__name__}: {excinfo.value}"
    )

def test_the_measurement_holds_at_pipeline_sizes_that_move_the_wrap(tmp_path):
    """G3, kept: the pipeline sizes at which 1.3.0's checker false-positived.

    A gate's first false positive is when it stops being read. 1.3.0's
    measurement reported one finding at 45 and 50 projects and none at 20,
    because the aggregate-impact bullet list wraps differently once the job
    counts gain a digit and the line it produced carried three bullets — each
    of which the old width function charged 0.761 em instead of 0.350. Nothing
    was ever off the page. These three sizes are the regression.
    """
    from nmtcapp.core.application import Application
    from nmtcapp.core.pipeline import Pipeline, PipelineProject
    from nmtcapp.renderers.pdf_builder import PDFApplicationBuilder
    from tests.test_rendered_output_baseline import (
        APPLICATION_ROUND, REQUESTED_ALLOCATION, _SPEC, _cde,
    )

    for n in (20, 45, 50):
        projects = []
        for i in range(n):
            (pid, name, city, state, sector, ptype, cost, qei, jobs, retained,
             units, sqft, tract, distress, eligible) = _SPEC[i % len(_SPEC)]
            p = PipelineProject(
                project_id=f"{pid}-{i:03d}", project_name=f"{name} {i:03d}",
                qalicb_name=f"{name} {i:03d} QALICB, LLC",
                address=f"{1100 + 25 * i} Commerce Street", city=city, state=state,
                sector=sector, project_type=ptype, total_project_cost=float(cost),
                qei_request=float(qei), qlici_amount=float(qei),
                expected_jobs_created=jobs, expected_jobs_retained=retained,
                expected_units_built=units, expected_sq_ft=sqft,
                closing_target_date=f"2099-{(i % 12) + 1:02d}-15",
                construction_start=f"2099-{(i % 12) + 1:02d}-28",
                operations_start=f"2100-{(i % 12) + 1:02d}-01",
            )
            p.census_tract, p.is_nmtc_eligible, p.distress_level = tract, eligible, distress
            p.is_native_area = p.is_high_migration_rural = p.is_us_territory = False
            p.is_opportunity_zone = p.is_persistent_poverty = p.is_below_market_rate = False
            p.is_unrelated_entity = p.geocode_success = True
            projects.append(p)
        pipeline = Pipeline(projects)
        pipeline.eligibility_data_status = "ok"

        app = Application(cde=_cde(), requested_allocation=REQUESTED_ALLOCATION,
                          application_round=APPLICATION_ROUND)
        app.add_pipeline(pipeline)
        path = str(tmp_path / f"n{n}.pdf")
        PDFApplicationBuilder(app, app.analyze()).save(path)

        findings, measured = check_pdf_frames(path)
        assert measured > 0, f"n={n}: nothing measured"
        assert not findings, (
            f"n={n} projects: {len(findings)} finding(s) out of {measured} "
            f"words. Before fixing anything here, establish whether the text "
            f"is off the page or the measurement is wrong — 1.3.0's was.\n\n"
            + "\n\n".join(findings)
        )


# ---------------------------------------------------------------------------
# G6: the renderer's frame and the gate's band are one statement
# ---------------------------------------------------------------------------

def test_the_renderer_lays_out_against_the_constants_this_gate_measures():
    """Change the renderer's margin and this fails, rather than the gate lying.

    ADDED IN 1.3.1 (G6). ``pdf_builder`` hardcoded ``0.9 * inch`` at five sites
    and ``inch``/``0.75 * inch`` at four more, while this gate measured against
    ``_frame_geometry``. Nothing tied them: moving the renderer's margin left
    the gate checking the old band, passing, while text sat in the footer.

    This reads the frames back off a real ``BaseDocTemplate`` rather than
    grepping for a literal, so it holds however the value is spelled.
    """
    from reportlab.lib.pagesizes import LETTER, landscape as rl_landscape
    from nmtcapp.renderers._frame_geometry import (
        BODY_MARGIN_INCHES, FRAME_BOTTOM_INCHES, LANDSCAPE_MARGIN_INCHES,
        POINTS_PER_INCH, frame_bounds, usable_width,
    )
    from nmtcapp.renderers.pdf_builder import PDFApplicationBuilder, _build_styles

    app = _baseline_application()
    builder = PDFApplicationBuilder(app, app.analyze())
    doc = builder._build_doc_template(_tmp_pdf_path())

    frames = {t.id: t.frames[0] for t in doc.pageTemplates}
    assert {"Cover", "Body", "Landscape"} <= set(frames), sorted(frames)

    page_w = float(LETTER[0])
    ls_w = float(rl_landscape(LETTER)[0])
    bottom = FRAME_BOTTOM_INCHES * POINTS_PER_INCH

    body = frames["Body"]
    assert (body._x1, body._y1) == (BODY_MARGIN_INCHES * POINTS_PER_INCH, bottom), (
        f"the portrait body frame sits at ({body._x1}, {body._y1}); "
        f"_frame_geometry says ({BODY_MARGIN_INCHES * POINTS_PER_INCH}, {bottom}). "
        "One of the two moved without the other."
    )
    assert (body._x1, body._x1 + body._width) == frame_bounds(page_w), (
        "frame_bounds() no longer describes the frame the renderer builds"
    )
    assert body._width == usable_width()

    ls = frames["Landscape"]
    ls_margin = LANDSCAPE_MARGIN_INCHES * POINTS_PER_INCH
    assert (ls._x1, ls._y1) == (ls_margin, bottom)
    assert (ls._x1, ls._x1 + ls._width) == frame_bounds(ls_w, landscape=True)
    assert ls._width == usable_width(landscape=True)

    assert doc.bottomMargin == bottom, (
        f"the doc template's bottomMargin is {doc.bottomMargin} and the frame "
        f"bottom is {bottom}. They were one literal typed twice."
    )


def test_the_chrome_exemption_is_a_bound_and_not_a_skip(rendered_pdf):
    """The footer's wider band covers the footer, and nothing else reaches it.

    ADDED IN 1.3.1 (G6). An exemption is a hole with a reason attached, and the
    reason has to be checkable. Two things are asserted:

      1. Every height the footer draws at is BELOW the body frame's bottom
         edge. If a footer baseline ever rose past it, the wider band would
         start covering story content and this gate would grant 18 pt of slack
         each side to the surface that actually clips.
      2. Every run on the page that is granted the wider band is a footer run
         — the CDE/round line or a page number — and nothing else on the page
         is drawn at a chrome baseline.

    Together those make the exemption a bound the gate fails if exceeded,
    rather than a height test anything low on the page can walk through.
    """
    from pypdf import PdfReader
    from nmtcapp.renderers._frame_geometry import (
        FOOTER_RULE_INCHES, FOOTER_TEXT_BASELINE_INCHES, POINTS_PER_INCH,
    )

    for label, inches in (("footer rule", FOOTER_RULE_INCHES),
                          ("footer text baseline", FOOTER_TEXT_BASELINE_INCHES)):
        assert inches * POINTS_PER_INCH < CHROME_BAND_TOP_PTS, (
            f"the {label} is drawn at {inches} in, at or above the body "
            f"frame's bottom edge. The footer band is 18 pt wider each side "
            "than the body frame; a chrome height inside the body frame hands "
            "that slack to story content."
        )

    exempted, body_runs = [], 0
    for page in PdfReader(rendered_pdf).pages:
        for run in positioned_runs(page):
            text = run["raw"].decode("latin-1").strip()
            if not text:
                continue
            if is_chrome_baseline(run["y"]):
                exempted.append(text)
            else:
                body_runs += 1

    assert body_runs > 0, "no body runs measured — this proof would be vacuous"
    assert exempted, (
        "no run was granted the footer band at all. Either the footer stopped "
        "rendering or the baselines drifted; an exemption nothing uses is an "
        "exemption nobody is checking."
    )
    strays = [t for t in exempted
              if not (t.startswith("Page ") or "CONFIDENTIAL" in t)]
    assert not strays, (
        f"{len(strays)} run(s) are drawn at a footer baseline and are not the "
        "footer. They are being measured against a band 18 pt wider each side "
        "than the frame they belong to:\n  " + "\n  ".join(repr(t) for t in strays[:10])
    )


def _tmp_pdf_path():
    import tempfile, os
    return os.path.join(tempfile.mkdtemp(), "template_probe.pdf")


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
