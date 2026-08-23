"""RENDERED-OUTPUT GATE 1 of 2: do two things on the chart overlap on screen?

WHY THIS CLASS OF GATE EXISTS (1.5.5 T6)

``tests/test_grade_threshold_twins.py`` asserts that the readiness chart's
threshold annotation CONTAINS the string "not a CDFI Fund threshold". It
does, and it did through 1.5.4, and on screen a reader saw:

    This tool's grade-B cut (70)
    not a CDF=80.0d threshold

The Completeness bar's value label was drawn on top of the disclaimer. The
CLAIM rendered; the DISCLAIMER was destroyed. Every test in this package
that touches that annotation reads the SOURCE STRING, and the source string
was never wrong.

AND THE DEFECT WAS DATA-DEPENDENT. The annotation sat at the top of the data
area; the collision happened because the topmost component scored 80.0 and
put its label at x = 81, inside the annotation's box. A pipeline with a
different completeness score does not collide. A single-fixture test would
have been green on most inputs -- so this gate sweeps a SPREAD of component
shapes chosen to walk every bar through the annotation's neighbourhood, and
asserts on measured bounding boxes rather than on strings.

  ⚠️  SCOPE LIMIT -- READ THIS BEFORE TRUSTING A GREEN FROM THIS FILE  ⚠️

  THIS GATE DOES NOT RUN A BROWSER. There is none in CI. It renders the
  figure with matplotlib's Agg backend and measures the bounding boxes
  matplotlib itself reports, in display coordinates, after a draw.

  IT THEREFORE OBSERVES:
    * whether the threshold annotation's box intersects any value label's
      box, or any bar's box, at the tested component shapes;
    * whether the band legend sits outside the data area;
    * geometry ONLY, for THIS ONE CHART.

  IT DOES **NOT** OBSERVE:
    * anything on a chart other than the readiness breakdown -- the Win
      Alignment and Optimizer charts are Plotly, rendered client-side, and
      nothing here can see them;
    * what a BROWSER does with the PNG Streamlit serves. Streamlit rescales
      the figure to the container width. Rescaling is affine on the whole
      image, so two boxes that do not intersect here do not begin to
      intersect there -- but that is an argument, not a measurement, and it
      is the one thing in this file that has not been executed;
    * text that is CLIPPED rather than overlapped, colour contrast,
      font fallback, or anything about the surrounding page;
    * component shapes outside SPREAD below. The sweep is dense around the
      annotation but it is a sample, not a proof over all inputs. The fix it
      guards is structural for exactly that reason: reserved headroom
      separates the bands by construction at every data value, so this gate
      is a check on the construction rather than the only thing standing
      between a reader and the defect.

  WHAT MAKES THE SWEEP NON-VACUOUS is ``test_legacy_layout_collides``: the
  1.5.4 placement is kept reachable behind ``legacy_layout=True`` and this
  file asserts it STILL FAILS. If a future change made the gate unable to
  see a collision, that test goes red rather than the suite going quietly
  green.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_REPO_ROOT), str(_REPO_ROOT / "streamlit_app")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from nmtcapp.data.schema import GRADE_THRESHOLDS
from readiness_chart import (
    ANNOTATION_HEADROOM,
    build_readiness_breakdown_figure,
    readiness_band_legend,
)

_COMPONENTS = (
    "eligibility_quality", "distress_concentration", "geographic_diversity",
    "impact_metrics", "validation_pass_rate", "completeness",
)

_B = GRADE_THRESHOLDS["B"]


def _shape(**overrides) -> dict:
    base = {k: 100.0 for k in _COMPONENTS}
    base.update(overrides)
    return base


#: Component shapes that walk every bar through the annotation's
#: neighbourhood. The annotation is anchored just right of the grade-B cut,
#: so a value label lands in its column when a component scores near it --
#: which is exactly what the shipped pipeline did at completeness 80.0.
SPREAD = [
    ("1.5.4 shipped sample (completeness 80.0 — the observed collision)",
     _shape(completeness=80.0, impact_metrics=38.2)),
    ("all components at the grade-B cut", _shape(**{k: float(_B) for k in _COMPONENTS})),
    ("all components just above the cut", _shape(**{k: _B + 1.0 for k in _COMPONENTS})),
    ("all components just below the cut", _shape(**{k: _B - 1.0 for k in _COMPONENTS})),
    ("all at zero", _shape(**{k: 0.0 for k in _COMPONENTS})),
    ("all at maximum", _shape(**{k: 100.0 for k in _COMPONENTS})),
    ("single component", {"completeness": 80.0}),
    ("two components", {"completeness": 80.0, "impact_metrics": 38.2}),
] + [
    (f"top component at {v:.1f}", _shape(completeness=float(v)))
    for v in range(60, 101, 2)
] + [
    (f"every component at {v:.1f}", _shape(**{k: float(v) for k in _COMPONENTS}))
    for v in range(60, 101, 5)
]


def _boxes(fig, parts):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    ann = parts["annotation"].get_window_extent(renderer)
    labels = [t.get_window_extent(renderer) for t in parts["value_labels"]]
    return ann, labels


def _overlap(a, b) -> bool:
    """True when two display-coordinate boxes share area."""
    return not (a.x1 <= b.x0 or b.x1 <= a.x0 or a.y1 <= b.y0 or b.y1 <= a.y0)


@pytest.mark.parametrize("name,scores", SPREAD, ids=[n for n, _ in SPREAD])
def test_annotation_never_overlaps_a_value_label(name, scores):
    """The disclaimer must not be overprinted, at any component shape."""
    fig, ax, parts = build_readiness_breakdown_figure(scores)
    try:
        ann, labels = _boxes(fig, parts)
        hits = [
            f"value label {t.get_text()!r} at {tuple(round(v) for v in (bb.x0, bb.y0, bb.x1, bb.y1))}"
            for t, bb in zip(parts["value_labels"], labels) if _overlap(ann, bb)
        ]
        assert not hits, (
            f"[{name}] the threshold annotation is overprinted — "
            "'not a CDFI Fund threshold' is the clause that gets destroyed:\n  "
            + "\n  ".join(hits)
        )
    finally:
        plt.close(fig)


@pytest.mark.parametrize("name,scores", SPREAD, ids=[n for n, _ in SPREAD])
def test_annotation_never_overlaps_a_bar(name, scores):
    """A bar drawn through the disclaimer destroys it just as thoroughly."""
    fig, ax, parts = build_readiness_breakdown_figure(scores)
    try:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        ann = parts["annotation"].get_window_extent(renderer)
        hits = [
            f"bar {i} ({p.get_width():.1f})"
            for i, p in enumerate(parts["bars"].patches)
            if _overlap(ann, p.get_window_extent(renderer))
        ]
        assert not hits, f"[{name}] bars drawn through the annotation: {hits}"
    finally:
        plt.close(fig)


def test_legacy_layout_collides():
    """THE GATE'S OWN PROOF OF LIFE.

    The 1.5.4 placement, at the shipped sample's component scores, must
    still be measured as a collision. If this ever passes, the gate has
    stopped being able to see the defect it exists for, and every green
    above it means nothing.
    """
    scores = _shape(completeness=80.0, impact_metrics=38.2)
    fig, ax, parts = build_readiness_breakdown_figure(scores, legacy_layout=True)
    try:
        ann, labels = _boxes(fig, parts)
        assert any(_overlap(ann, bb) for bb in labels), (
            "the 1.5.4 layout no longer collides under measurement — either "
            "matplotlib's text metrics changed or this gate has gone blind"
        )
    finally:
        plt.close(fig)


def test_legacy_layout_is_not_reachable_from_the_page():
    """``legacy_layout`` is a test affordance and must never ship on a surface."""
    page = (_REPO_ROOT / "streamlit_app" / "pages" / "1_Pipeline_Analyzer.py").read_text()
    assert "legacy_layout" not in page


def test_headroom_is_a_positive_clearance():
    """The structural claim the fix rests on, stated as an assertion.

    ``ANNOTATION_HEADROOM`` is the gap kept between the top of the topmost
    bar and the BOTTOM of the annotation, enforced by measurement in
    ``_fit_annotation_headroom``. If it were ever reduced to zero the
    separation would depend on rounding, and the defect would return for
    some data shape the SPREAD above does not contain.
    """
    assert ANNOTATION_HEADROOM > 0, "headroom must be a real clearance"


class TestBandLegend:
    """T5 — the colours encode a house band and must say so."""

    def test_every_drawn_colour_has_a_legend_entry(self):
        from readiness_chart import _score_color
        legend_colors = {c for c, _ in readiness_band_legend()}
        drawn = {_score_color(v) for v in
                 [0, 10, 39, 54, 55, 69, 70, 84, 85, 99, 100]}
        assert drawn <= legend_colors, (
            f"colours drawn with no legend entry: {drawn - legend_colors}"
        )

    def test_legend_labels_say_whose_bands_these_are(self):
        fig, ax, parts = build_readiness_breakdown_figure(_shape(completeness=80.0))
        try:
            legend = ax.get_legend()
            assert legend is not None, "bar colours encode a band with no legend"
            title = legend.get_title().get_text()
            assert "this tool's" in title.lower()
            assert "not cdfi fund" in title.lower().replace("—", "").replace("-", " ")
        finally:
            plt.close(fig)

    def test_legend_sits_outside_the_data_area(self):
        """A legend inside the axes is one more artist competing with the bars."""
        fig, ax, parts = build_readiness_breakdown_figure(
            _shape(completeness=80.0, impact_metrics=38.2))
        try:
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            legend_bb = ax.get_legend().get_window_extent(renderer)
            axes_bb = ax.get_window_extent(renderer)
            assert not _overlap(legend_bb, axes_bb), (
                "the band legend overlaps the plotting area"
            )
        finally:
            plt.close(fig)

    def test_band_boundaries_are_the_live_constants(self):
        labels = " ".join(t for _, t in readiness_band_legend())
        for key in ("A", "B", "C"):
            # ``:g`` matches how the legend renders them — GRADE_THRESHOLDS
            # holds floats and the labels drop the trailing ".0", so
            # str(85.0) would look for "85.0" in a label that reads "85+".
            assert f"{GRADE_THRESHOLDS[key]:g}" in labels, (
                f"grade {key} cut {GRADE_THRESHOLDS[key]} is not in the legend — "
                "the legend must be interpolated from GRADE_THRESHOLDS, not typed"
            )
