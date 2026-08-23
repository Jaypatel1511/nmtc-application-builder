"""The readiness-breakdown bar chart, extracted so its GEOMETRY can be gated.

WHY THIS IS A MODULE AND NOT TWENTY LINES INSIDE THE PAGE (1.5.5 T2/T6)

It was twenty lines inside the page, and the annotation that disclaims the
70-point line spent a release being overprinted by a bar's value label. A
reader of 1.5.4 saw:

    This tool's grade-B cut (70)
    not a CDF=80.0d threshold

``This tool's grade-B cut (70)`` — THE CLAIM — survived. ``not a CDFI Fund
threshold`` — THE DISCLAIMER — did not. That is the same asymmetry 1.5.3
found when the deduction table was truncated: when rendering degrades, the
qualifier is what degrades.

AND IT WAS DATA-DEPENDENT, which is why 1,422 tests, a hostile audit and an
audit close all missed it. The annotation sat at x = 70.5 at the TOP of the
axes; the Completeness bar happened to score 80.0, putting its value label at
x = 81 on the topmost row — straight through the annotation's second line.
Move that one component and the defect vanishes. No fixture-based test would
ever have found it, and none did.

THE FIX IS GEOMETRIC, NOT COSMETIC. The annotation is no longer placed
"near the top of the data area" and hoped for. A band of RESERVED HEADROOM is
added above the topmost bar and the annotation is drawn inside it. Value
labels are drawn at bar centres, so no bar's label can enter that band at any
data value — the separation holds by construction rather than by luck, which
is the only kind of fix a data-dependent defect can have.

Gated by ``tests/test_readiness_chart_geometry.py``, which measures RENDERED
bounding boxes across a spread of component shapes chosen to sweep every bar
through the annotation's neighbourhood.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from chart_style import (
    ACCENT, DANGER, MID_BLUE, NEUTRAL, SUCCESS, TEXT_DARK,
    style_matplotlib_axes,
)
from nmtcapp.data.schema import GRADE_THRESHOLDS

#: Blank space, in category units, kept between the top of the topmost bar
#: and the BOTTOM of the threshold annotation.
#:
#: A FIXED HEADROOM IS NOT ENOUGH, and finding that out is why this constant
#: is a clearance rather than an offset. The annotation is two lines of 8pt
#: text: its height in DISPLAY units is fixed, so its height in DATA units
#: depends on the y-limits, which is what we are trying to choose. Anchoring
#: it a fixed number of category units above the bars left it overlapping the
#: top bar at six components -- measured, not guessed, and it is why
#: ``_fit_annotation_headroom`` below solves for the limit instead.
ANNOTATION_HEADROOM = 0.35

#: Bar half-height. Bars are drawn at height 0.6 centred on y = 0 .. n-1, so
#: the topmost bar's ink reaches y = n - 1 + BAR_HALF_HEIGHT and every value
#: label is drawn at a bar CENTRE, i.e. never above y = n - 1.
BAR_HALF_HEIGHT = 0.3

#: Bottom of the y axis. Unchanged from 1.5.4.
Y_MIN = -0.6


def _fit_annotation_headroom(fig, ax, annotation, top_bar_top: float) -> None:
    """Raise the y limit until the annotation clears the bars, and verify it.

    Solved by MEASUREMENT rather than assumed, because the quantity that
    decides it -- the annotation's height expressed in data units -- is a
    function of the y limit being chosen. Each pass measures the actual
    rendered box, computes the shortfall, and lifts the top by exactly that
    much; the shortfall shrinks geometrically because lifting the top also
    stretches the data span the text is measured against.

    The loop is bounded. If it has not converged it leaves the axes at the
    most generous limit it reached, and
    ``tests/test_readiness_chart_geometry.py`` measures the result rather
    than trusting this function to have succeeded.
    """
    target = top_bar_top + ANNOTATION_HEADROOM
    for _ in range(8):
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        box = annotation.get_window_extent(renderer)
        corners = ax.transData.inverted().transform(
            [(box.x0, box.y0), (box.x1, box.y1)])
        ann_bottom = min(corners[0][1], corners[1][1])
        shortfall = target - ann_bottom
        if shortfall <= 0:
            return
        lo, hi = ax.get_ylim()
        new_top = hi + shortfall
        ax.set_ylim(lo, new_top)
        annotation.set_position((annotation.get_position()[0], new_top))

#: Right-hand limit of the x axis. The value labels sit at score + 1, so a
#: 100.0 label starts at 101 and needs room to its right.
X_MAX = 118


def readiness_band_legend() -> tuple:
    """``(colour, label)`` for each band the bar colours encode.

    THE COLOURS WERE AN UNLABELLED CLASSIFICATION (1.5.5 T5). Through 1.5.4
    this chart drew bars green, blue and red by value with NO legend
    anywhere. A reader could see that 80 was a different colour from 100 and
    had no way to learn what the difference meant. The page's "unsourced
    house heuristic" caption covers the NUMBERS; it said nothing about the
    colour scheme, so the one part of the chart a reader decodes fastest was
    the one part with no disclosure attached.

    Labelled rather than dropped, on the ground that the bands are not new
    information: they ARE ``schema.GRADE_THRESHOLDS``, which this same page
    already prints in words as "Overall readiness grade". Dropping the colour
    would remove a legible encoding of something the tool asserts anyway;
    labelling it discloses what was already being claimed silently. The
    labels say whose bands they are, because they are this tool's and not the
    CDFI Fund's — the Fund publishes no readiness score, so it publishes no
    grade bands on this axis.
    """
    # ``:g`` rather than str(): GRADE_THRESHOLDS holds floats, so a plain
    # interpolation renders "A (85.0+)" and "B (70.0-84.0)" on a chart whose
    # axis is labelled in whole numbers. Read from the constant either way --
    # the point of 1.5.2 T4 was that these bounds are never re-typed.
    a, b, c = GRADE_THRESHOLDS["A"], GRADE_THRESHOLDS["B"], GRADE_THRESHOLDS["C"]
    return (
        (SUCCESS, f"A ({a:g}+)"),
        (MID_BLUE, f"B ({b:g}–{a - 1:g})"),
        (ACCENT, f"C ({c:g}–{b - 1:g})"),
        (DANGER, f"below C (<{c:g})"),
    )


def _score_color(score: float) -> str:
    # THREE HAND-TYPED NUMBERS, TWO OF THEM TWINS OF A LIVE CONSTANT (1.5.2
    # T4). This ladder read ``50 / 70 / 85``. The 70 and the 85 are
    # GRADE_THRESHOLDS["B"] and ["A"] re-typed, and the 50 was an ORPHAN --
    # it is not a grade cut at all (C is 55, D is 40), so the colour boundary
    # a CDE saw on this chart matched no band this package defines anywhere.
    # The ladder is now one statement: deleting GRADE_THRESHOLDS cannot leave
    # this chart drawing bands that no longer exist.
    if score < GRADE_THRESHOLDS["C"]:
        return DANGER
    if score < GRADE_THRESHOLDS["B"]:
        return ACCENT
    if score < GRADE_THRESHOLDS["A"]:
        return MID_BLUE
    return SUCCESS


def build_readiness_breakdown_figure(component_scores: dict, *, legacy_layout: bool = False):
    """Build the readiness bar chart and return ``(fig, ax, parts)``.

    ``parts`` carries the artists a geometry gate needs to measure:
    ``{"annotation": Text, "value_labels": [Text, ...], "bars": BarContainer}``.

    ``legacy_layout=True`` reproduces the 1.5.4 placement EXACTLY, including
    the defect. It exists so ``tests/test_readiness_chart_geometry.py`` can
    prove itself RED against the shipped behaviour instead of asserting that
    a fix it cannot see the absence of is present. It is never used by the
    app; ``test_legacy_layout_is_not_reachable_from_the_page`` holds that.

    Example::

        fig, ax, parts = build_readiness_breakdown_figure(
            {"completeness": 80.0, "impact_metrics": 38.2}
        )
    """
    labels = [k.replace("_", " ").title() for k in component_scores]
    scores = [round(float(v), 1) for v in component_scores.values()]
    colors = [_score_color(s) for s in scores]

    fig, ax = plt.subplots(figsize=(8, max(3, len(labels) * 0.55)))
    bars = ax.barh(labels, scores, color=colors, height=0.6)

    b_cut = GRADE_THRESHOLDS["B"]
    ax.axvline(x=b_cut, color=NEUTRAL, linestyle="--", linewidth=1.2, alpha=0.8)

    value_labels = []
    for bar, score in zip(bars, scores):
        value_labels.append(ax.text(
            score + 1, bar.get_y() + bar.get_height() / 2, f"{score:.1f}",
            va="center", ha="left", fontsize=9, color=TEXT_DARK,
        ))

    ax.set_xlim(0, X_MAX)

    # "COMPETITIVE" WAS A CLAIM ABOUT THE FUND WITH NO FUND REFERENT (1.5.2
    # T4). This line was drawn at a hardcoded 70 and labelled "Competitive
    # (70)". The CDFI Fund publishes no readiness score and no grade, so it
    # publishes no competitiveness bar on this axis. What survives is the
    # true statement: 70 is where THIS TOOL's grade B begins -- interpolated,
    # so the line and the label cannot drift from the constant.
    note = f"This tool's grade-B cut ({b_cut:.0f})\nnot a CDFI Fund threshold"

    if legacy_layout:
        # 1.5.4 VERBATIM. Placed at 98% of the data area's top, INSIDE the
        # rows -- so whether it collided with a value label depended on what
        # the topmost component happened to score.
        annotation = ax.text(b_cut + 0.5, ax.get_ylim()[1] * 0.98, note,
                             color=NEUTRAL, fontsize=8, va="top", ha="left")
    else:
        # RESERVED HEADROOM. The annotation is anchored at the TOP of the
        # axes and the top of the axes is then raised until the annotation's
        # measured box clears the topmost bar. Value labels are drawn at bar
        # CENTRES, strictly below the bar tops, so clearing the bars clears
        # every label too -- at every data value, not just the sampled ones.
        # No bar moves; only empty space is added above them.
        top_bar_top = len(labels) - 1 + BAR_HALF_HEIGHT
        top = top_bar_top + ANNOTATION_HEADROOM
        ax.set_ylim(Y_MIN, top)
        annotation = ax.text(b_cut + 0.5, top, note,
                             color=NEUTRAL, fontsize=8, va="top", ha="left")

    style_matplotlib_axes(ax, xlabel="Score (0–100)")

    if not legacy_layout:
        # OUTSIDE THE DATA AREA on purpose: a legend placed inside would be
        # one more artist competing with bars whose lengths are data, which
        # is the defect this chart is being repaired for.
        handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c, _ in readiness_band_legend()]
        texts = [t for _, t in readiness_band_legend()]
        ax.legend(handles, texts, loc="upper center", bbox_to_anchor=(0.5, -0.18),
                  ncol=4, frameon=False, fontsize=8,
                  title="This tool's readiness grade bands — not CDFI Fund thresholds",
                  title_fontsize=8)

    fig.tight_layout()
    if not legacy_layout:
        _fit_annotation_headroom(fig, ax, annotation,
                                 len(labels) - 1 + BAR_HALF_HEIGHT)
    return fig, ax, {"annotation": annotation, "value_labels": value_labels, "bars": bars}
