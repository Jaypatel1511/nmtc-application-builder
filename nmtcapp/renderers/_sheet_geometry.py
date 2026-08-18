"""How tall a wrapped spreadsheet row has to be to display its own text.

WHY THIS MODULE EXISTS (1.3.0 B1)
=================================

The Summary Dashboard's metrics loop set ``row_dimensions[row].height = 18``
for every row, uniformly. 1.3.0 S4 then gave row 12 a two-line label — the
distress cell's denominator disclosure — and the row kept its one-line height.
Measured in Excel 16.112 against an autofit replica at the shipped geometry:

    A12 label   needs 30.0 pt   ships 18.0 pt   -> line 2 never displayed

The visible text ended mid-negation, at "(a share of QEI, not", and the half
that never displayed was the pointer to the basis note. The round's own remedy
was invisible on the surface it was written for.

THE BASELINE CANNOT SEE THIS. tests/rendered_baseline/excel.txt records
``Summary Dashboard!A12|str|fmt=General|<text>`` — cell values, number formats
and nothing else. Row heights, column widths and merges are structurally
outside it, the same shape as the interpolation mask that hid every printed
constant until 1.2.1 built tests/pinned_constants.txt as a separate gate. A
correct fix to B1 leaves excel.txt byte-unchanged. So this module exists to be
the thing a gate can assert against: tests/test_excel_geometry.py re-derives
every dashboard row's required height from the SHIPPED workbook — its actual
cell text, its actual merged span, its actual font size — and fails when a
height cannot display its own label.

MERGED CELLS DO NOT AUTOFIT. This is the whole reason a height has to be
computed rather than delegated. Excel's AutoFit is a no-op on a merged range,
and every label on the dashboard is merged (A:B for the metrics rows, A:F for
the notes). There is no "let Excel decide" option available here.

THE CONSTANTS ARE MEASURED, NOT ASSUMED
=======================================

Every constant below was measured in Microsoft Excel 16.112 (macOS) by opening
a generated workbook and autofitting an UNMERGED replica cell set to the same
point width and font size — the standard technique, because autofit works
there and not on the merged original. The raw runs:

    column width      openpyxl 22.0 -> 132.0 pt   openpyxl 18.0 -> 108.0 pt
                      openpyxl 12.0 ->  72.0 pt
                      => POINTS_PER_WIDTH_UNIT = 6.0, exactly, on three points

    autofit ladder    span 240 pt, font 10, text of N repeated "wwww " tokens
                      N*5 =   5,  25 chars -> 16.0 pt   (one line, floored)
                      N*5 =  45,  50,  55 -> 30.0 pt    (two lines)
                      N*5 =  90,  95, 100 -> 45.0 pt    (three lines)
                      N*5 = 145 -> 75.0   190 -> 90.0   235 -> 105.0
                      => 15.0 pt per wrapped line at font 10
                      => a one-line row still floors at 16.0 pt, which is the
                         default font's line height, not the cell font's

    line height       the same ladder at span 564 pt for every font size the
                      builder uses. Each column of heights was an exact
                      multiple of one value, given here:
                      f8 -> 12.0  f9 -> 14.0  f10 -> 15.0
                      f11 -> 16.0 f13 -> 19.0 f16 -> 23.0
                      => LINE_HEIGHT_BY_FONT_SIZE. The ratios to font size are
                         1.50/1.56/1.50/1.45/1.46/1.44, so no single multiplier
                         is right; see the constant.

    shipped strings   the four wrapped labels on the dashboard, autofitted at
                      their real spans (this model's estimate in brackets):
                      A12  93 chars  240 pt  f10 -> 30.0  [30.0, exact]
                      A25 311 chars  564 pt  f8  -> 25.0  [36.0, +11.0]
                      A27  88 chars  564 pt  f9  -> 16.0  [16.0, exact]
                      A28   3013 ch  564 pt  f8  -> 217.0 [264.0, +47.0]

CHAR_WIDTH_FACTOR = 0.5 is the average advance width of Calibri as a fraction
of its point size. It was chosen from that last table: it is the largest value
that never UNDER-estimates any of the four real strings, and it reproduces
Excel exactly on the two that are one and two lines. It over-estimates on long
prose, which costs a few points of unused row and is the safe direction — a
row taller than its text displays the text.

WHAT THIS MODEL IS NOT. It is not Excel's line breaker. It counts characters
against an average advance width; Excel measures real glyphs. It will disagree
with Excel by a line on text whose character mix is far from English prose,
always by making the row taller. It is a floor on the height a row needs, not
a prediction of what autofit would return, and the gate asserts against it as
a floor. Recalibrating it means opening a workbook in Excel again and redoing
the table above — not editing a number here.
"""
from __future__ import annotations

import math

#: Excel points per unit of openpyxl ``column_dimensions[x].width``.
#: Measured on three columns of the shipped dashboard; exact, not fitted.
POINTS_PER_WIDTH_UNIT = 6.0

#: Height of one WRAPPED line, in points, per font size. Measured directly in
#: Excel 16.112 by autofitting an unmerged 564-pt cell against strings long
#: enough to force 2-16 lines and reading the step; every observed height was
#: an exact multiple of the value below (font 8 carries a further +1 pt of
#: cell padding, which MIN_ROW_HEIGHT absorbs).
#:
#:     font  8 ->  12.0      font  9 ->  14.0      font 10 -> 15.0
#:     font 11 ->  16.0      font 13 ->  19.0      font 16 -> 23.0
#:
#: IT IS NOT A CONSTANT RATIO, which is why this is a table and not one number.
#: The ratios are 1.50, 1.56, 1.50, 1.45, 1.46 and 1.44 — Excel derives a line
#: box from real font metrics and rounds it to whole points, so a single
#: multiplier is wrong somewhere no matter which one is chosen. A 1.5 factor
#: was tried first and over-predicted font 11 by a point, which reported the
#: dashboard's own section headings as clipped when they are not: a gate's
#: first false positive is the moment it starts being ignored.
LINE_HEIGHT_BY_FONT_SIZE = {
    8: 12.0, 9: 14.0, 10: 15.0, 11: 16.0, 13: 19.0, 16: 23.0,
}

#: Fallback for a font size nobody has measured. Deliberately the highest ratio
#: in the table above, rounded up, so an unmeasured size errs toward a taller
#: row. Adding a size to the renderer means measuring it and adding it above,
#: not relying on this.
LINE_HEIGHT_FALLBACK_FACTOR = 1.6

#: Average glyph advance, as a fraction of the font's point size. See the
#: module docstring for how this was chosen and why it errs high.
CHAR_WIDTH_FACTOR = 0.5

#: What AUTOFIT returns for a single short line, whatever the cell's font:
#: measured at 16.0 for a one-line font-9 label rather than 13.5, because
#: autofit floors at the DEFAULT font's line height.
#:
#: IT IS NOT A REQUIREMENT AND required_row_height DOES NOT APPLY IT. That
#: distinction cost a false positive: with 16.0 imposed as a floor, this gate
#: reported the appendix sheets' row-2 subtitle — 72 characters of font 8, one
#: line, in a row explicitly set to 14 — as clipped. It is not clipped. Font 8
#: has a 12-point line box, and Excel draws a 14-point row exactly as told.
#: The floor describes what Excel PICKS when nobody tells it; the requirement
#: is what the text needs to be visible, and those are different numbers.
#: A gate's first false positive is the moment it starts being ignored.
MIN_ROW_HEIGHT = 16.0

#: Excel's own hard ceiling on a row height.
MAX_ROW_HEIGHT = 409.0


def span_points(*widths: float) -> float:
    """Total width in points of a merged span, from openpyxl column widths.

    Example::

        span_points(22.0, 18.0)   # -> 240.0, the dashboard's A:B label span
    """
    return POINTS_PER_WIDTH_UNIT * sum(widths)


def chars_per_line(span_pts: float, font_size: float) -> int:
    """How many characters of ``font_size`` text fit across ``span_pts``.

    Example::

        chars_per_line(240.0, 10)   # -> 48
    """
    return max(1, int(span_pts // (CHAR_WIDTH_FACTOR * font_size)))


def wrapped_line_count(text: str, cpl: int) -> int:
    """Lines a greedy word-wrap needs for ``text`` at ``cpl`` chars per line.

    Greedy rather than ``len(text) // cpl`` because the two disagree exactly
    where it matters. A label is a handful of long words, so where it breaks
    depends on the words; ``//`` silently under-counts every line that had to
    break early, which is the arithmetic that produced 1.3.0's 275-pt guess
    for a 217-pt note. A word longer than the line is broken across lines,
    the way Excel breaks one.

    Example::

        wrapped_line_count("aaa bbb ccc", 7)   # -> 2
    """
    lines = 0
    for para in text.split("\n"):
        words = para.split()
        if not words:
            lines += 1
            continue
        lines += 1
        used = 0
        for word in words:
            needed = len(word) if used == 0 else len(word) + 1
            if used + needed <= cpl:
                used += needed
                continue
            while len(word) > cpl:
                lines += 1
                word = word[cpl:]
            lines += 1
            used = len(word)
    return lines


def required_row_height(text, span_pts: float, font_size: float) -> float:
    """Minimum row height, in points, that displays ``text`` in full.

    NOT CLAMPED TO :data:`MAX_ROW_HEIGHT`, deliberately. A return above that
    ceiling means the text no longer fits in ONE Excel row at this width and
    has to be split across rows — a decision for a person, not a silent
    truncation to 409 that would clip the tail of a disclosure and leave every
    height check passing. The builder clamps when it writes; the gate asserts
    against this unclamped value and fails loudly if the ceiling is reached.

    Returns 0.0 for empty or non-string values: an empty cell requires no
    height at all, and whatever the row is set to is enough for it.

    Example::

        required_row_height("a" * 93, 240.0, 10)   # -> 30.0
    """
    if not isinstance(text, str) or not text.strip():
        return 0.0
    lines = wrapped_line_count(text, chars_per_line(span_pts, font_size))
    line_height = LINE_HEIGHT_BY_FONT_SIZE.get(
        int(font_size), math.ceil(LINE_HEIGHT_FALLBACK_FACTOR * font_size)
    )
    return float(math.ceil(lines * line_height))


def fits_one_row(text, span_pts: float, font_size: float) -> bool:
    """Whether ``text`` can be displayed in a single Excel row at this width.

    Example::

        fits_one_row("short", 564.0, 9)   # -> True
    """
    return required_row_height(text, span_pts, font_size) <= MAX_ROW_HEIGHT
