"""Where a PDF flowable is allowed to be, in points.

WHY THIS MODULE EXISTS (1.3.0 FIX-2 B1)
=======================================

``pdf_builder`` recomputed ``page_w - 2 * margin`` at four call sites and let a
fifth — ``_content_to_flowables``, the generic ``table_ref`` renderer every
section key/value table passes through — compute nothing at all. That fifth
site called ``Table(data)`` with no ``colWidths``, so ReportLab sized its
columns to the longest single line and drew a 17,197-pt table into a 432-pt
frame.

A width that is recomputed at each call site is a width one call site can
forget. This module is the single statement of it, and the gate
(``tests/test_render_frame_geometry.py``) measures against the same numbers the
builder lays out against, so the two cannot drift.

THE TWO BANDS, AND WHY A GATE HAS TO KNOW BOTH
==============================================

Portrait pages carry text in two different horizontal bands, at two different
margins, and neither is wrong:

    body frame      1.25 in each side (``PAGE_LAYOUT["margin_left"]``), set by
                    ``PDFApplicationBuilder.save``. Everything in the story is
                    laid into this.
    header/footer   1.00 in each side, drawn straight onto the canvas by
                    ``_make_header_footer``. Wider on purpose: the footer rule
                    is meant to run past the text column.

A gate that checks everything against the body frame reports the page number on
every page as clipped — a false positive on sixteen of twenty pages, which is
the moment a gate stops being read. A gate that checks everything against the
chrome margin gives away 18 pt of slop on the surface that actually clips. So
both are stated here, and the band is chosen by height: chrome is drawn below
:data:`CHROME_BAND_TOP_PTS`, which is the body frame's own bottom edge.

Landscape pages use one margin for both bands (0.75 in), so the distinction
costs nothing there and is kept only so the caller does not have to know.
"""
from __future__ import annotations

from nmtcapp.renderers.styles import PAGE_LAYOUT

#: PostScript points per inch. ReportLab's ``lib.units.inch``, restated so this
#: module imports with no ReportLab installed — the Word and Markdown paths
#: must keep working on a machine that has neither.
POINTS_PER_INCH = 72.0

#: US Letter, the only page size this package renders.
PORTRAIT_PAGE_WIDTH_PTS = 8.5 * POINTS_PER_INCH      # 612.0
LANDSCAPE_PAGE_WIDTH_PTS = 11.0 * POINTS_PER_INCH    # 792.0

#: The body frame's side margin, in inches, per orientation. Portrait reads
#: ``PAGE_LAYOUT`` rather than restating 1.25, so a style change moves the
#: frame and the gate together.
BODY_MARGIN_INCHES = PAGE_LAYOUT["margin_left"]
LANDSCAPE_MARGIN_INCHES = 0.75

#: The running header/footer's side margin, in inches. Deliberately narrower
#: than the portrait body margin; see the module docstring.
CHROME_MARGIN_INCHES = 1.0

#: The body frame's bottom edge, in inches — and therefore the height below
#: which anything drawn is header/footer chrome rather than story content.
#:
#: ONE STATEMENT, FIVE FORMER CALL SITES (1.3.1 G6). ``pdf_builder`` hardcoded
#: ``0.9 * inch`` at five places — the portrait frame's origin and height, the
#: landscape frame's origin and height, and the doc template's ``bottomMargin``
#: — while the gate measured against this module. Nothing tied them. Moving the
#: renderer's margin left the gate measuring the old band, silently, and the
#: failure mode is a gate that passes while text sits in the footer.
FRAME_BOTTOM_INCHES = 0.9
CHROME_BAND_TOP_PTS = FRAME_BOTTOM_INCHES * POINTS_PER_INCH   # 64.8

#: The two heights the running footer draws at, in inches: the rule, and the
#: text baseline of the CDE/round line and the page number.
#:
#: THE EXEMPTION IS A BOUND, NOT A SKIP (1.3.1 G6). The chrome band is 18 pt
#: wider each side than the body frame, and a gate that hands that extra slack
#: to anything drawn below :data:`CHROME_BAND_TOP_PTS` hands it to a body
#: flowable that happens to land low on the page too. These two heights are
#: what the footer actually draws at, so the gate can grant the wider band to
#: runs AT them and refuse it to everything else — and
#: ``test_the_chrome_exemption_is_a_bound_and_not_a_skip`` fails if a height
#: here ever rises past the frame bottom, which is the only way the exemption
#: could start covering story content.
FOOTER_RULE_INCHES = 0.65
FOOTER_TEXT_BASELINE_INCHES = 0.45

#: Heights, in points, at which a text run is running-footer chrome. The rule
#: is not here: it is a line, and no text is drawn at it.
CHROME_TEXT_BASELINES_PTS = (FOOTER_TEXT_BASELINE_INCHES * POINTS_PER_INCH,)   # (32.4,)

#: How far off a chrome baseline a run may sit and still be chrome. ReportLab
#: writes coordinates into the content stream at 2 decimal places.
CHROME_BASELINE_TOLERANCE_PTS = 0.5


def is_chrome_baseline(y_pts: float) -> bool:
    """True when a run drawn at this height is running-footer chrome.

    Example::

        is_chrome_baseline(32.4)   # -> True, the footer text baseline
        is_chrome_baseline(60.0)   # -> False, below the frame but not chrome
    """
    return any(abs(y_pts - b) <= CHROME_BASELINE_TOLERANCE_PTS
               for b in CHROME_TEXT_BASELINES_PTS)


def usable_width(*, landscape: bool = False) -> float:
    """Width available to a flowable inside the body frame, in points.

    Example::

        usable_width()                  # -> 432.0, the portrait text column
        usable_width(landscape=True)    # -> 684.0
    """
    if landscape:
        return LANDSCAPE_PAGE_WIDTH_PTS - 2 * LANDSCAPE_MARGIN_INCHES * POINTS_PER_INCH
    return PORTRAIT_PAGE_WIDTH_PTS - 2 * BODY_MARGIN_INCHES * POINTS_PER_INCH


def frame_bounds(page_width_pts: float, *, landscape: bool = False) -> tuple:
    """Left and right edges of the body frame on a page of this width.

    Example::

        frame_bounds(612.0)   # -> (90.0, 522.0)
    """
    margin = (LANDSCAPE_MARGIN_INCHES if landscape else BODY_MARGIN_INCHES) * POINTS_PER_INCH
    return margin, page_width_pts - margin


def chrome_bounds(page_width_pts: float, *, landscape: bool = False) -> tuple:
    """Left and right edges of the running header/footer band.

    Example::

        chrome_bounds(612.0)   # -> (72.0, 540.0)
    """
    margin = (LANDSCAPE_MARGIN_INCHES if landscape else CHROME_MARGIN_INCHES) * POINTS_PER_INCH
    return margin, page_width_pts - margin
