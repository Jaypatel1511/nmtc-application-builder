"""A figure or a URL in the PDF is one token, or the reader is misled.

TWO DEFECTS, ONE MECHANISM (1.7.1 R3, R4). Measured on the published 1.7.0
PDF with pypdf:

    p.16   $124,700,00        p.25   $155,000,00
           0                          0 total prior

    p.26   ... publishes at https://www.cdfifund.gov/pro
           grams-training/programs/new-markets-tax-credit/apply-step

``$124,700,00`` reads as ``$124,700.00``: $124.7 million rendered as
something a reviewer reads as $124,700, on a TOTAL row, three orders of
magnitude out, in a document filed with a federal agency. Six sites. And the
one URL that reaches the CY 2026 Application Materials — the page the note
itself tells the reader to go and re-verify against — copy-pastes broken.

THE MECHANISM, instrumented rather than assumed. ``_df_to_rl_table`` passes
``colWidths=None`` for the portrait appendices, so ReportLab divides the
frame equally: six columns of a 432 pt frame, less the frame's 6 pt padding
each side, is 70 pt a column, 60 pt inside the cell padding. The bold
``$122,500,000`` measures 61.2 pt at 10 pt Helvetica-Bold. And ReportLab's
``ParagraphStyle.splitLongWords`` defaults to 1: a single token wider than
its line is broken at whatever character fits. Widening the column moves the
threshold and leaves the defect for a larger figure, which is why the fix is
two things — no cell style may split a token, and an auto-sized column is
at least as wide as its widest token — and why this gate renders a pipeline
whose totals are TEN TIMES the baseline's, so a column sized for today's
figures is not evidence.

THE PROOF THIS GATE CAN FAIL. Run on the 1.7.0 renderer before the fix:

    test_no_pdf_line_ends_in_a_partial_digit_group[baseline]  RED  (8 sites)
    test_no_pdf_line_ends_in_a_partial_digit_group[wide]      RED (17 sites)
    test_every_census_tract_appears_whole[baseline]           RED
    test_the_application_materials_url_is_one_token           RED
    test_every_currency_total_appears_whole                   green — the
        same total also prints whole in Section D's key/value table, so
        this is the PRESENCE half of the pair and not evidence on its own.

And with only half the fix in place (measured, and the first attempt at
this record predicted the second line wrong — the frame gate does NOT see
an overflow that stays inside the table, which is why
``test_no_table_cell_is_wider_than_its_column`` exists):

    splitLongWords restored, derived widths kept   -> green on both
        fixtures: the derived widths alone keep every token inside its
        column. (Before _TOKEN_SAFETY_PTS this reddened on a 61.2 pt total
        in a 61.2 pt cell — an exact fit ReportLab rounds the other way.)
    equal widths restored, splitLongWords=0 kept   -> the text gates green,
        test_no_table_cell_is_wider_than_its_column RED: eight cells in the
        landscape appendix, GEOIDs and headers, drawn past their cell.
    So the widths are the load-bearing half for tables, and the
    cell-overflow check is the gate for the case the text gates cannot see.

    WHAT splitLongWords=0 IS NOT. An earlier draft of this docstring called
    it load-bearing for the URL (R4). A hostile audit falsified that by
    mutation: flipping it 0 -> 1 on styles["body"], on cell_style and on
    header_style leaves every gate GREEN at all three sites. _fit_urls
    shrinks the URL to 10 pt -- 387.9 pt in a 420 pt column -- so it always
    fits and the flag never fires for it. The load-bearing pair is
    _auto_col_widths and _fit_urls; reverting BOTH reproduces the 1.7.0 cut
    at ``https://www.cdfifund.gov/pro``. splitLongWords=0 is retained as
    defence in depth, not as a half of the fix, and the claim that it is
    one was a sentence nobody had mutated.

Two-sided: the absence of the split line AND the presence of the whole
figure are asserted separately, because a document that stopped printing
the total would pass the first alone.
"""
from __future__ import annotations

import re

import pytest

from nmtcapp.tables.pipeline_table import CURRENCY_COLUMNS

#: A line whose last token is a dollar figure cut inside a digit group:
#: "$124,700,00", "$155,000,0". Any comma-separated group shorter than three
#: digits at end of line is a cut, never a legitimate rendering.
_PARTIAL_GROUP_AT_EOL = re.compile(r"\$[\d,]*\d,\d{1,2}$")


def _pdf_lines(path: str) -> list:
    from pypdf import PdfReader
    lines = []
    for page in PdfReader(path).pages:
        lines.extend((page.extract_text() or "").splitlines())
    return lines


def _application(scale: float):
    from nmtcapp.core.application import Application
    from tests.test_rendered_output_baseline import (
        APPLICATION_ROUND, REQUESTED_ALLOCATION, _cde, _pipeline,
    )

    pipeline = _pipeline()
    for p in pipeline:
        p.total_project_cost *= scale
        p.qei_request *= scale
        p.qlici_amount *= scale
    app = Application(cde=_cde(), requested_allocation=REQUESTED_ALLOCATION * scale,
                      application_round=APPLICATION_ROUND)
    app.add_pipeline(pipeline)
    return app


@pytest.fixture(scope="module", params=["baseline", "wide"])
def rendered_pdf(request, tmp_path_factory):
    """The baseline fixture, and the same fixture at ten times the dollars."""
    scale = 1.0 if request.param == "baseline" else 10.0
    app = _application(scale)
    out = str(tmp_path_factory.mktemp(f"pdf_{request.param}"))
    paths = app.generate(out, formats=["pdf"])
    assert "pdf" in paths, "the PDF renderer produced nothing"
    return app, paths["pdf"]


def test_no_pdf_line_ends_in_a_partial_digit_group(rendered_pdf):
    _app, path = rendered_pdf
    lines = _pdf_lines(path)
    cuts = []
    for i, line in enumerate(lines):
        if _PARTIAL_GROUP_AT_EOL.search(line.strip()):
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            cuts.append(f"{line.strip()!r} -> {nxt!r}")
    assert not cuts, (
        f"{len(cuts)} dollar figure(s) are cut inside a digit group at a line "
        "end. Each reads as a figure a thousand times smaller:\n  "
        + "\n  ".join(cuts)
    )


def test_every_currency_total_appears_whole(rendered_pdf):
    """The other side: the totals ARE in the document, as single tokens."""
    from nmtcapp.tables.pipeline_table import build_pipeline_table

    app, path = rendered_pdf
    text = "\n".join(_pdf_lines(path))
    df = build_pipeline_table(app.pipeline, app.cde)
    totals = df.iloc[-1]
    assert str(totals.iloc[0]).upper().startswith("TOTAL"), "last row is not the totals row"
    expected = []
    for col in ("QEI Request ($)", "Total Project Cost ($)"):
        assert col in CURRENCY_COLUMNS
        value = totals[col]
        expected.append(f"${float(value):,.0f}")
    assert all(len(e) >= len("$10,000,000") for e in expected), (
        f"fixture totals {expected} are too narrow to have split; the gate "
        "would pass vacuously"
    )
    missing = [e for e in expected if e not in text]
    assert not missing, f"totals absent from the PDF as whole tokens: {missing}"


def test_every_census_tract_appears_whole(rendered_pdf):
    """Found while fixing R3: Appendix B cut 11-digit GEOIDs the same way.

    The 1.7.0 baseline carried ``360290067`` over ``02`` for tract
    36029006702 — a federal identifier a reviewer would look up, split by the
    equal-width landscape table at 7 pt. Same mechanism, same fix, its own
    assertion so a regression in the landscape appendix cannot hide behind
    the portrait totals passing.
    """
    app, path = rendered_pdf
    text = "\n".join(_pdf_lines(path))
    tracts = sorted({p.census_tract for p in app.pipeline if p.census_tract})
    assert len(tracts) >= 5, "fixture carries too few tracts to be evidence"
    assert all(len(t) == 11 and t.isdigit() for t in tracts), tracts
    missing = [t for t in tracts if t not in text]
    assert not missing, f"census tracts absent from the PDF as whole tokens: {missing}"
    lines = _pdf_lines(path)
    cut = [ln.strip() for ln in lines if re.fullmatch(r"\d{9,10}", ln.strip())]
    assert not cut, f"9- or 10-digit runs on their own line — a cut GEOID: {cut}"


def test_the_application_materials_url_is_one_token(rendered_pdf):
    from nmtcapp.renderers._round_provenance import UPCOMING_APPLICATION_PAGE_URL

    _app, path = rendered_pdf
    lines = _pdf_lines(path)
    whole = [ln for ln in lines if UPCOMING_APPLICATION_PAGE_URL in ln]
    assert whole, (
        "the CY 2026 Application Materials URL does not appear on any one "
        "line of the PDF. A reader who copies it gets a broken link to the "
        "one page the note tells them to re-verify against. Lines carrying "
        "a fragment: "
        + repr([ln.strip() for ln in lines if "cdfifund.gov/pro" in ln])
    )


def cell_overflows(story, portrait_avail: float, landscape_avail: float) -> list:
    """Every table cell whose wrapped text is wider than its column.

    MODELLED, NOT EXTRACTED — the hole the text gates cannot see. With
    ``splitLongWords=0`` a token that does not fit is not cut; it is drawn
    past its cell's right padding into the next cell. That leaves no cut for
    the extractor to find and lands inside the table's own bounds, so
    ``tests/test_render_frame_geometry`` cannot see it either (measured: equal
    widths plus ``splitLongWords=0`` passed both). So ask ReportLab directly:
    wrap each cell Paragraph at the width its column will draw at, and read
    the per-line ``extraSpace`` — negative means the line is wider than the
    space it was given.

    Example::

        cell_overflows(builder._build_story(styles), 432.0, 684.0)   # -> []
    """
    from reportlab.platypus import NextPageTemplate, Paragraph, Table

    findings = []
    avail = portrait_avail
    for item in story:
        if isinstance(item, NextPageTemplate):
            name = item.action[1]
            name = name[0] if isinstance(name, (list, tuple)) else name
            avail = landscape_avail if name == "Landscape" else portrait_avail
            continue
        if not isinstance(item, Table):
            continue
        item.wrap(avail, 10_000)
        widths = list(item._colWidths)
        style_cmds = getattr(item, "_cellStyles", None)
        for r, row in enumerate(item._cellvalues):
            for c, cell in enumerate(row):
                # Table.wrap re-wraps each flowable cell in a one-element
                # tuple; the Paragraph is inside it.
                if isinstance(cell, (tuple, list)) and len(cell) == 1:
                    cell = cell[0]
                if not isinstance(cell, Paragraph):
                    continue
                cs = style_cmds[r][c] if style_cmds else None
                pad = (cs.leftPadding + cs.rightPadding) if cs else 10.0
                inner = widths[c] - pad
                cell.wrap(inner, 10_000)
                lines = getattr(cell.blPara, "lines", [])
                for line in lines:
                    extra = line[0] if isinstance(line, tuple) else getattr(line, "extraSpace", 0.0)
                    # ReportLab's own line breaker lets a multi-word line
                    # run ~0.1 pt over; a digit is ~5.5 pt. Half a point is
                    # below anything a reader could see and above the fuzz.
                    if extra < -0.5:
                        findings.append(
                            f"row {r} col {c} {cell.text[:40]!r}: wrapped line is "
                            f"{-extra:.1f} pt wider than its {inner:.1f} pt cell"
                        )
                        break
    return findings


def test_no_table_cell_is_wider_than_its_column(rendered_pdf):
    from nmtcapp.renderers._frame_geometry import usable_width
    from nmtcapp.renderers.pdf_builder import PDFApplicationBuilder, _build_styles
    from tests.test_excel_geometry import _analysis_in_state

    app, _path = rendered_pdf
    builder = PDFApplicationBuilder(app, _analysis_in_state(app.analyze(), "nominal"))
    findings = cell_overflows(builder._build_story(_build_styles()),
                              usable_width(), usable_width(landscape=True))
    assert not findings, (
        f"{len(findings)} table cell(s) draw wider than their column — a token "
        "that no longer splits now overlaps its neighbour:\n  " + "\n  ".join(findings)
    )


def test_the_overflow_checker_sees_an_overflowing_cell():
    """The modelled check is only evidence if it can find one."""
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, Table

    style = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=10, splitLongWords=0)
    tbl = Table([[Paragraph("$1,254,500,000", style), Paragraph("x", style)]],
                colWidths=[40, 40])
    assert cell_overflows([tbl], 432.0, 684.0), "a 74 pt token in a 30 pt cell was not reported"
    wide = Table([[Paragraph("$1,254,500,000", style), Paragraph("x", style)]],
                 colWidths=[120, 40])
    assert cell_overflows([wide], 432.0, 684.0) == []


def test_the_gate_sees_the_1_7_0_cut():
    """The regex is evidence only if it matches what shipped."""
    assert _PARTIAL_GROUP_AT_EOL.search("$124,700,00")
    assert _PARTIAL_GROUP_AT_EOL.search("TOTALS 20 projects $155,000,00")
    assert not _PARTIAL_GROUP_AT_EOL.search("$124,700,000")
    assert not _PARTIAL_GROUP_AT_EOL.search("$1,254,500,000")
