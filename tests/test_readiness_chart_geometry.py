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
    * what a BROWSER does with the PNG Streamlit serves -- but the pipeline
      that produces that PNG HAS now been measured, and this note used to
      describe a pipeline that does not run. It said "Streamlit rescales the
      figure to the container width", and Streamlit does no such thing.
      ``streamlit/elements/pyplot.py`` sets
      ``{"bbox_inches": "tight", "dpi": 200, "format": "png"}`` and calls
      ``fig.savefig(image, **kwargs)``: a RE-RASTERISATION at twice this
      gate's dpi with a recomputed canvas bbox. The browser then CSS-scales
      the finished raster, which is a pure bitmap scale and cannot move one
      glyph relative to another.

      MEASURED IN THIS REPOSITORY, over the same SPREAD below, comparing the
      annotation against every value label and every bar
      (``_measured_clearances`` at the foot of this module re-derives both
      lines on demand):

          gate      (dpi 100, draw)              : 38 shapes, 0 collisions,
                                                   min clearance 10.26 px
          STREAMLIT (dpi 200, bbox_inches=tight) : 38 shapes, 0 collisions,
                                                   min clearance 22.51 px

      CLEARANCE GROWS. It does NOT grow by exactly two, and the difference is
      not noise: the ratio is 2.195. Layout scales linearly with dpi, but TEXT
      EXTENTS DO NOT -- font hinting makes a glyph box slightly sub-linear
      (the annotation's own box scales 1.928 in height and 1.948 in width), so
      the text shrinks a little relative to the layout and the gap between
      them opens by more than the dpi factor. ``bbox_inches="tight"``
      contributes nothing to this: it is a CROP, and the relative geometry is
      identical with and without it, measured both ways.

      SO THE CONCLUSION TRANSFERS, and it now transfers as a measurement
      rather than as an argument: the tighter of the two pipelines is the one
      this file tests. What is still NOT measured is the browser -- font
      fallback if the served page substitutes a face, and CSS scaling that is
      not uniform. Those are outside a PNG and outside CI;
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

import functools
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


#: How far BELOW the grade-B cut the dense sweep starts, in score points.
#:
#: THE SWEEP FOLLOWS THE THRESHOLD (1.5.5 audit B5). It was hardcoded to
#: ``range(60, 101, 2)`` while the annotation's x position tracks
#: ``GRADE_THRESHOLDS["B"]``, which is 70 today. Re-base B to 45 and the sweep
#: would go on walking 60..100 -- above the annotation's whole neighbourhood --
#: while every test in this file stayed green over a region where nothing can
#: collide. A sweep that no longer sweeps the place the defect lives is the
#: "green means nothing" shape this suite keeps finding.
#:
#: Ten below and up to the ceiling reproduces the original 60..100 exactly at
#: B = 70, and moves with B. Asymmetric on purpose: a value label is drawn to
#: the RIGHT of its bar and the annotation is anchored just right of the cut,
#: so the collision region extends upward from B, not downward.
_SWEEP_BELOW = 10
_SWEEP_MAX = 100


def _sweep(step: int) -> list:
    """Scores from ``_B - _SWEEP_BELOW`` to 100, clamped to a real score."""
    start = int(max(0, _B - _SWEEP_BELOW))
    return list(range(start, _SWEEP_MAX + 1, step))


_DENSE_SWEEP = _sweep(2)
_COARSE_SWEEP = _sweep(5)


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
    for v in _DENSE_SWEEP
] + [
    (f"every component at {v:.1f}", _shape(**{k: float(v) for k in _COMPONENTS}))
    for v in _COARSE_SWEEP
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


# ---------------------------------------------------------------------------
# T6's THESIS, APPLIED TO THE THING THE READER ACTUALLY OPENS (1.5.5 audit B2)
# ---------------------------------------------------------------------------
#
# THE DEFECT. Everything above measures ``readiness_chart.py``. A reader does
# not open ``readiness_chart.py``; they open the Pipeline Analyzer page. Until
# this gate, NOTHING TIED THE TWO TOGETHER. The 1.5.5 audit reverted
# ``pages/1_Pipeline_Analyzer.py`` to the 1.5.4 inline chart -- annotation at
# ``ax.get_ylim()[1] * 0.98``, no reserved headroom, no band legend -- left
# ``readiness_chart.py`` untouched, and THE WHOLE SUITE STAYED GREEN. Every
# measurement above went on passing, against a module the page no longer used.
#
# ``test_legacy_layout_is_not_reachable_from_the_page`` is the only existing
# page-side check and it asserts that ONE SUBSTRING is absent. Absence of
# "legacy_layout" says nothing about what the page draws; the 1.5.4 inline
# chart contains no such string either.
#
# NOT A STRING SEARCH, DELIBERATELY. The last three attempts at a page gate in
# this repository were satisfiable by a comment. This one is a DATA-FLOW
# assertion on the parsed page:
#
#     the readiness breakdown data -- whatever is read out of
#     ``.component_scores`` -- may reach ``build_readiness_breakdown_figure``
#     and may be tested for emptiness, and may go NOWHERE ELSE.
#
# That is "constructs no other readiness chart inline" stated as a property
# rather than as a blacklist of the shapes one mutation happened to use. The
# 1.5.4 chart fails it at ``breakdown.items()``, before it ever reaches
# ``plt.subplots``; so does any future inline chart, whatever it is built out
# of, because a chart cannot be drawn from data it never touches.
#
# WHY NOT "the page must not call plt.subplots". Page 1 legitimately builds
# four other matplotlib charts -- benchmark, states, sector, jobs per $1MM --
# and none of them is a readiness chart. A rule that forbade figure creation
# would be wrong four times over and would be deleted the first time somebody
# added a fifth.
#
# THE OTHER PAGES ARE CHECKED THE SAME WAY, which is the half this repository
# has learned to expect: every previous widening of a page gate immediately
# found a second instance. This time it did NOT -- pages 2 and 4 draw no
# charts at all, page 3 is Plotly, and page 1 is the only reader of
# ``component_scores``. That is a measurement, not an assumption: the gate
# walks every page and app.py, so a SECOND page that starts drawing readiness
# data inline is caught on the day it appears rather than on the day somebody
# widens a gate again.

_READINESS_ATTR = "component_scores"
_GATED_BUILDER = "build_readiness_breakdown_figure"


def _streamlit_surfaces() -> list:
    """Every Streamlit page and the app entry point, as (label, path)."""
    app_dir = _REPO_ROOT / "streamlit_app"
    paths = sorted((app_dir / "pages").glob("*.py")) + [app_dir / "app.py"]
    return [(str(p.relative_to(_REPO_ROOT)), p) for p in paths if p.is_file()]


def _readiness_bindings(tree) -> dict:
    """``{variable: lineno}`` for every name bound from ``.component_scores``.

    The RHS is walked whole rather than pattern-matched, because the live
    binding is a conditional expression --
    ``rs.component_scores if hasattr(rs, "component_scores") else {}`` -- and
    a matcher that only understood a bare attribute would miss it and report
    the page clean.

    Example::

        _readiness_bindings(ast.parse("b = rs.component_scores"))
    """
    import ast as _ast
    bound = {}
    for node in _ast.walk(tree):
        if not (isinstance(node, _ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], _ast.Name)):
            continue
        if any(isinstance(sub, _ast.Attribute) and sub.attr == _READINESS_ATTR
               for sub in _ast.walk(node.value)):
            bound[node.targets[0].id] = node.lineno
    return bound


def _disallowed_uses(tree, variable: str) -> list:
    """Uses of ``variable`` that are neither an emptiness test nor the builder.

    Example::

        _disallowed_uses(ast.parse("if b: pass"), "b")   # -> []
    """
    import ast as _ast

    permitted = set()
    for node in _ast.walk(tree):
        # ``build_readiness_breakdown_figure(breakdown)`` -- positional or
        # keyword, so the gate does not turn on the call style.
        if isinstance(node, _ast.Call):
            func = node.func
            name = func.id if isinstance(func, _ast.Name) else getattr(func, "attr", None)
            if name == _GATED_BUILDER:
                for arg in list(node.args) + [kw.value for kw in node.keywords]:
                    if isinstance(arg, _ast.Name) and arg.id == variable:
                        permitted.add(id(arg))
        # ``if breakdown:`` / ``while breakdown:`` -- an emptiness test reads
        # the name without touching the data.
        for test in ("test",):
            candidate = getattr(node, test, None)
            if isinstance(candidate, _ast.Name) and candidate.id == variable:
                permitted.add(id(candidate))
        if isinstance(node, _ast.BoolOp):
            for value in node.values:
                if isinstance(value, _ast.Name) and value.id == variable:
                    permitted.add(id(value))
        if isinstance(node, _ast.UnaryOp) and isinstance(node.op, _ast.Not) \
                and isinstance(node.operand, _ast.Name) \
                and node.operand.id == variable:
            permitted.add(id(node.operand))

    offenders = []
    for node in _ast.walk(tree):
        if not (isinstance(node, _ast.Name) and node.id == variable
                and isinstance(node.ctx, _ast.Load)):
            continue
        if id(node) not in permitted:
            offenders.append(node.lineno)
    return offenders


def test_the_page_gets_its_readiness_chart_from_the_gated_module():
    """The surface the reader opens must use the module this file measures.

    Everything above is a measurement of ``readiness_chart.py``. This is the
    assertion that the page is still reading it.
    """
    import ast as _ast

    users, missing_call = [], []
    for label, path in _streamlit_surfaces():
        tree = _ast.parse(path.read_text(), filename=str(path))
        if not _readiness_bindings(tree):
            continue
        users.append(label)
        calls = {
            (n.func.id if isinstance(n.func, _ast.Name) else getattr(n.func, "attr", None))
            for n in _ast.walk(tree) if isinstance(n, _ast.Call)
        }
        if _GATED_BUILDER not in calls:
            missing_call.append(label)

    assert users, (
        f"no Streamlit surface reads .{_READINESS_ATTR} at all. Either the "
        "readiness breakdown was removed from the app -- in which case this "
        "gate and the geometry sweep above are both measuring a chart nobody "
        "renders -- or the page walk is broken and this file is passing over "
        "nothing."
    )
    assert not missing_call, (
        f"these surfaces read .{_READINESS_ATTR} but never call "
        f"{_GATED_BUILDER}(): {missing_call}.\n\n"
        "Every geometry assertion in this file measures that function. A page "
        "that draws the readiness breakdown any other way is unmeasured, and "
        "the green above says nothing about what the reader sees."
    )


def test_no_streamlit_surface_builds_a_readiness_chart_inline():
    """Readiness data may reach the gated builder and nothing else.

    THE MUTATION THIS CATCHES is the audit's: revert the page to the 1.5.4
    inline chart and leave ``readiness_chart.py`` alone. It fails here at
    ``breakdown.items()`` -- the data being handled by the page at all -- so
    the gate does not depend on recognising ``plt.subplots``, ``barh``,
    ``axvline`` or any other shape the replacement happens to use.
    """
    import ast as _ast

    offenders = []
    for label, path in _streamlit_surfaces():
        tree = _ast.parse(path.read_text(), filename=str(path))
        for variable, lineno in _readiness_bindings(tree).items():
            for use in _disallowed_uses(tree, variable):
                offenders.append(
                    f"{label}:{use}: {variable!r} (bound from "
                    f".{_READINESS_ATTR} at line {lineno})"
                )

    assert not offenders, (
        "a Streamlit page handles readiness breakdown data itself instead of "
        f"passing it to {_GATED_BUILDER}():\n  " + "\n  ".join(offenders)
        + "\n\nThe geometry of that chart is gated in readiness_chart.py and "
          "measured by this file. A chart built in the page body cannot be "
          "measured -- nothing can render a Streamlit page body and read back "
          "a bounding box -- so drawing it there is drawing it ungated. Pass "
          f"the data to {_GATED_BUILDER}() and extend that function instead."
    )


# ---------------------------------------------------------------------------
# THE SCOPE NOTE'S OWN CLAIMS, AS ASSERTIONS (1.5.5 audit B5)
# ---------------------------------------------------------------------------
#
# The header used to concede that the browser-rescale case was "an argument,
# not a measurement". It also described the wrong pipeline: Streamlit does not
# rescale the figure to the container, it RE-RASTERISES with
# ``fig.savefig(image, bbox_inches="tight", dpi=200, format="png")``. Both are
# fixed there. What follows keeps the correction honest -- the numbers in that
# note are re-derived by code in this file rather than remembered, and the
# claim that the served pipeline is the SLACKER of the two is asserted rather
# than asserted-about.


def _clearance(a, b) -> float:
    """Smallest display-space gap between two boxes; negative when overlapping.

    Example::

        _clearance(box_a, box_b) > 0
    """
    return max(max(b.x0 - a.x1, a.x0 - b.x1), max(b.y0 - a.y1, a.y0 - b.y1))


@functools.lru_cache(maxsize=None)
def _measured_clearances(dpi: int, tight: bool) -> tuple:
    """``(collisions, min_clearance)`` over the whole SPREAD at one dpi.

    ``tight`` runs Streamlit's actual call first, so the measurement is taken
    against a figure that has been through it rather than one that has not.

    Example::

        _measured_clearances(100, False)
    """
    import io

    collisions, worst = 0, float("inf")
    for _name, scores in SPREAD:
        fig, _ax, parts = build_readiness_breakdown_figure(scores)
        try:
            if tight:
                fig.savefig(io.BytesIO(), bbox_inches="tight", dpi=dpi,
                            format="png")
            fig.set_dpi(dpi)
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            ann = parts["annotation"].get_window_extent(renderer)
            others = (
                [t.get_window_extent(renderer) for t in parts["value_labels"]]
                + [p.get_window_extent(renderer) for p in parts["bars"].patches]
            )
            for box in others:
                if _overlap(ann, box):
                    collisions += 1
                worst = min(worst, _clearance(ann, box))
        finally:
            plt.close(fig)
    return collisions, worst


def test_the_dense_sweep_still_brackets_the_grade_b_cut():
    """Move ``GRADE_THRESHOLDS["B"]`` and the sweep must move with it.

    THE RESIDUAL THIS CLOSES. The sweep was ``range(60, 101, 2)`` -- a literal
    -- while the annotation is anchored at ``_B``. At B = 70 those coincide.
    Re-base B and the old sweep would have gone on walking a region the
    annotation had left, with every assertion in this file passing over a
    neighbourhood where nothing can collide.

    Bracketing is the property that matters: values on BOTH sides of the cut,
    and a step fine enough that a value label lands in the annotation's column.
    """
    below = [v for v in _DENSE_SWEEP if v < _B]
    above = [v for v in _DENSE_SWEEP if v > _B]
    assert below and above, (
        f"the dense sweep {_DENSE_SWEEP[:3]}..{_DENSE_SWEEP[-1]} does not "
        f"bracket the grade-B cut ({_B}). The annotation is anchored there; a "
        "sweep that does not cross it is not sweeping the collision region."
    )
    assert min(above) - _B <= 2 and _B - max(below) <= 2, (
        f"the sweep steps over the grade-B cut ({_B}) with nothing within two "
        f"points of it: nearest below {max(below)}, nearest above {min(above)}."
    )


def test_the_scope_notes_clearance_figures_are_reproducible():
    """The two lines quoted in this module's scope limit, re-derived.

    A gate's own scope note may not carry a number nobody in this repository
    derived. These are that derivation, run.
    """
    gate_collisions, gate_clearance = _measured_clearances(100, tight=False)
    assert gate_collisions == 0
    assert gate_clearance == pytest.approx(10.26, abs=0.75), (
        f"the gate pipeline's minimum clearance is now {gate_clearance:.2f} px, "
        "not the 10.26 recorded in this module's scope limit. Re-measure and "
        "update the note -- a scope limit quoting a stale number is the shape "
        "this file exists to stop."
    )


def test_the_streamlit_pipeline_is_the_slacker_of_the_two():
    """Streamlit's own savefig call, measured -- not reasoned about.

    ``streamlit/elements/pyplot.py`` passes
    ``{"bbox_inches": "tight", "dpi": 200, "format": "png"}``. This runs that
    call and asserts what the old scope note could only argue: nothing that
    clears here begins to collide there.

    The ratio is NOT exactly two, and that is recorded rather than rounded
    away. Layout scales linearly with dpi; text extents do not, because font
    hinting makes a glyph box slightly sub-linear. The gap therefore opens by
    somewhat MORE than the dpi factor -- which is the safe direction, and the
    reason the assertion below is an inequality rather than an equality.
    """
    gate_collisions, gate_clearance = _measured_clearances(100, tight=False)
    st_collisions, st_clearance = _measured_clearances(200, tight=True)

    assert gate_collisions == 0 and st_collisions == 0, (
        f"collisions: gate {gate_collisions}, streamlit {st_collisions}"
    )
    assert st_clearance > gate_clearance, (
        f"the pipeline Streamlit actually runs (dpi 200, bbox_inches='tight') "
        f"clears by {st_clearance:.2f} px against this gate's "
        f"{gate_clearance:.2f} px. If that ever inverts, THIS FILE IS NO "
        "LONGER TESTING THE TIGHTER CASE and its greens stop transferring to "
        "what the reader sees."
    )
