"""Every workbook label must fit the row it is drawn in (1.3.0 B1).

THE DEFECT THIS GATE EXISTS FOR
===============================

1.3.0 S4 added a denominator disclosure to the Summary Dashboard's distress
label and a basis note to carry the rest of the argument. The metrics loop set
``row_dimensions[row].height = 18`` for every row, uniformly, so the two-line
label kept a one-line height. Measured in Excel 16.112 at the shipped geometry:
A12 needed 30.0 pt and shipped 18.0. The visible text ended mid-negation —

    Deep/Severe Distress Concentration (a share of QEI, not

— and the half that never displayed was the pointer to the note. The round's
own remedy was invisible on the surface it was written for.

WHY THE RENDERED BASELINE COULD NOT CATCH IT, AND CANNOT PROVE THE FIX
======================================================================

tests/rendered_baseline/excel.txt records::

    Summary Dashboard!A12|str|fmt=General|<text>

Cell coordinates, Python types, number formats, values. Row heights, column
widths and merge ranges appear nowhere in it, so the entire class is invisible
to that gate — not under-tested, structurally unreachable. A correct fix to B1
leaves excel.txt byte-unchanged, which is why a byte-unchanged baseline is not
evidence here.

This is the same shape as the interpolation mask that hid every printed
constant until 1.2.1 built tests/pinned_constants.txt as a separate gate, and
the same shape as the value-only projection that hid B-3's number formats until
the excel_cell_formats surface was added. Third instance. The remedy is the
same one: a gate that reads the dimension the other gate cannot see.

WHAT THIS GATE ASSERTS

It loads the SHIPPED workbook and, for every text cell that carries a label,
re-derives the height that text needs from the file's own geometry — the actual
string, the actual merged span, the actual font size — and fails if the row is
shorter. It reads nothing from the builder, so a height hardcoded anywhere, a
column narrowed, a font enlarged, or a label lengthened all fail it.

It also asserts no label needs MORE than Excel's 409-pt row ceiling, because a
row cannot grow past that: text needing more is text that will clip however the
height is set, and has to be split across rows by a person.

THE GATE'S OWN SENSITIVITY IS TESTED. ``test_checker_catches_the_1_3_0_defect``
rebuilds B1 exactly — a two-line label at ``height = 18`` — and asserts the
checker flags it. A gate that cannot fail is the recurring defect of this
package; this one is made to fail on demand, in CI, next to the gate itself.
"""
from __future__ import annotations

import pytest

pytest.importorskip("openpyxl", reason="openpyxl not installed")

import openpyxl
from openpyxl.utils import get_column_letter

from nmtcapp.renderers._sheet_geometry import (
    MAX_ROW_HEIGHT, MIN_ROW_HEIGHT, required_row_height, span_points,
)
from nmtcapp.renderers.excel_builder import ExcelApplicationBuilder

#: EVERY sheet. This started as just the two hand-laid-out sheets, excluded
#: the six DataFrame ones with the reasoning "_write_df_to_sheet does not set
#: row heights at all, so those rows keep Excel's default and autofit applies
#: normally" — and that reasoning was FALSE. _write_df_to_sheet set
#: ``row_dimensions[row_num].height = 16`` for every data row, uniformly, the
#: same hardcoded height in the same shape as the metrics loop's 18, forty
#: lines above a column auto-sizer that had not run yet.
#:
#: Measured on the shipped sample before the fix: Investor Commitments!G6 held
#: the 351-character "[CDE TO COMPLETE: This table is a blank form ...]"
#: instruction in a 40-wide column at height 16 — one line of nine — and
#: Distress Documentation!N8 clipped the ACS vintage off "CDFI Fund NMTC
#: Eligibility Table (2016-2020 ACS)". The audit found B1 on one sheet; the
#: same defect was live on six more, and the first draft of this gate was
#: written to look away from them.
#:
#: So: no exclusions. A sheet this gate does not read is a sheet where the
#: next uniform height goes unnoticed.
LAID_OUT_SHEETS = None  # every sheet in the workbook


def _merged_span_points(ws, cell) -> float:
    """Width in points of the merged range anchored at ``cell``, or of its column."""
    for rng in ws.merged_cells.ranges:
        if rng.min_row == cell.row and rng.min_col == cell.column:
            widths = []
            for col in range(rng.min_col, rng.max_col + 1):
                dim = ws.column_dimensions[get_column_letter(col)]
                # openpyxl reports None for a column never explicitly sized;
                # Excel's default is 8.43 characters.
                widths.append(dim.width if dim.width else 8.43)
            return span_points(*widths)
    dim = ws.column_dimensions[get_column_letter(cell.column)]
    return span_points(dim.width if dim.width else 8.43)


def check_sheet_geometry(ws) -> list:
    """Return one finding per label that cannot display in its own row.

    Example::

        assert check_sheet_geometry(wb["Summary Dashboard"]) == []
    """
    findings = []
    for row in ws.iter_rows():
        for cell in row:
            if not isinstance(cell.value, str) or not cell.value.strip():
                continue
            font_size = float(cell.font.size or 11)
            span = _merged_span_points(ws, cell)
            needed = required_row_height(cell.value, span, font_size)
            # An UNSET height is not a height of 16 — it is the absence of a
            # customHeight flag, which is Excel's instruction to autofit the
            # row on render. Those rows cannot clip and are not this gate's
            # business; only a height somebody chose can be too small.
            shipped = ws.row_dimensions[cell.row].height
            if not shipped:
                continue
            shipped = float(shipped)
            if needed > MAX_ROW_HEIGHT:
                findings.append(
                    f"{ws.title}!{cell.coordinate} needs {needed:.1f} pt, which "
                    f"is past Excel's {MAX_ROW_HEIGHT:.0f} pt row ceiling. No "
                    f"height can display it; split it across rows. "
                    f"({len(cell.value)} chars at {span:.0f} pt wide, "
                    f"font {font_size:g})"
                )
            elif shipped + 0.01 < needed:
                findings.append(
                    f"{ws.title}!{cell.coordinate} ships {shipped:.1f} pt and "
                    f"needs {needed:.1f} pt — the label is clipped and the "
                    f"reader sees only part of it. "
                    f"({len(cell.value)} chars at {span:.0f} pt wide, "
                    f"font {font_size:g}) {cell.value[:70]!r}"
                )
    return findings


@pytest.fixture
def workbook(sample_application, application_analysis):
    return ExcelApplicationBuilder(sample_application, application_analysis).build()


def test_every_label_fits_its_row(workbook):
    """No label anywhere in the workbook may be taller than its own row."""
    findings = []
    for ws in workbook.worksheets:
        findings.extend(check_sheet_geometry(ws))
    assert not findings, (
        f"{len(findings)} label(s) do not fit their rows. This is 1.3.0 B1's "
        "class: a string that is correct in the source and clipped on the "
        "page. tests/rendered_baseline/excel.txt cannot see it — it records "
        "cell values, not geometry — so this gate is the only thing that "
        "can.\n\n" + "\n\n".join(findings)
    )


def test_the_distress_label_carries_its_whole_disclosure(workbook):
    """B1's own cell, named, so a regression reads as itself and not as drift."""
    ws = workbook["Summary Dashboard"]
    label = next(
        (c.value for c in ws["A"]
         if isinstance(c.value, str)
         and c.value.startswith("Deep/Severe Distress Concentration")),
        None,
    )
    assert label is not None, "the distress label is gone from the dashboard"
    assert "not of QLICIs" in label, (
        "the distress label no longer states its own denominator. That "
        "disclosure is the reason the row exists in this gate."
    )
    assert not check_sheet_geometry(ws), (
        "the dashboard's distress label does not fit its row — see "
        "test_every_label_fits_its_row"
    )


def test_checker_catches_the_1_3_0_defect(workbook):
    """Rebuild B1 and prove the checker fails on it.

    A gate that has never been seen to fail is a gate nobody has evidence
    about. This restores exactly what shipped — a two-line label at
    ``height = 18`` — and asserts the checker reports it.
    """
    ws = workbook["Summary Dashboard"]
    target = next(
        c for c in ws["A"]
        if isinstance(c.value, str)
        and c.value.startswith("Deep/Severe Distress Concentration")
    )
    assert not check_sheet_geometry(ws), "sheet must be clean before the defect"

    original = ws.row_dimensions[target.row].height
    try:
        ws.row_dimensions[target.row].height = 18  # the shipped 1.3.0 value
        findings = check_sheet_geometry(ws)
        assert findings, (
            "the checker did not flag a two-line label at a one-line height — "
            "it cannot catch the defect it exists for"
        )
        assert any(f"A{target.row}" in f and "ships 18.0 pt" in f
                   for f in findings), findings
    finally:
        ws.row_dimensions[target.row].height = original

    assert not check_sheet_geometry(ws), "the defect must not outlive this test"


def test_the_basis_note_is_reachable_by_name(workbook):
    """The dashboard's pointer must name something the workbook actually has.

    1.3.0 S4's pointer said "see the basis note below" and pointed fifteen rows
    down, past the readiness block and under the footer, at a row number
    nothing on screen names — and whether "below" was even visible depended on
    the reader's window, because the file stores no window geometry at all.
    """
    from nmtcapp.renderers._question_25 import Q25_BASIS_SHEET_NAME

    ws = workbook["Summary Dashboard"]
    label = next(
        c.value for c in ws["A"]
        if isinstance(c.value, str)
        and c.value.startswith("Deep/Severe Distress Concentration")
    )
    assert Q25_BASIS_SHEET_NAME in label, (
        "the distress label does not name the sheet its basis note is on"
    )
    assert Q25_BASIS_SHEET_NAME in workbook.sheetnames, (
        f"the label points at a sheet named {Q25_BASIS_SHEET_NAME!r} that this "
        "workbook does not contain"
    )
    assert workbook.sheetnames.index(Q25_BASIS_SHEET_NAME) == 1, (
        "the basis note sheet must sit immediately after the Summary "
        "Dashboard — a pointer is only as good as how far the reader looks"
    )
