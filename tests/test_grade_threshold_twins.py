"""T4 (1.5.2) — GRADE_THRESHOLDS may not be re-typed onto a rendered chart.

THE FINDING, AND IT WAS ALREADY WRITTEN DOWN. ``tests/pinned_constants.txt``'s
WAIVE row for ``schema.GRADE_THRESHOLDS`` has said since 1.5.1 that 70 is
"DRAWN ON A STREAMLIT CHART, where streamlit_app/pages/1_Pipeline_Analyzer.py
hardcodes an axvline at 70 labelled 'Competitive (70)' beside a _score_color
ladder that re-types 50/70/85", and it closed: **"no gate reads either."**

A defect a registry has recorded and no test asserts is a defect with a
paper trail and no brake. This is the brake.

TWO DISTINCT PROBLEMS LIVED IN THOSE FOUR LINES.

  1. THE DUPLICATION (the L-3 class). 70 and 85 are ``GRADE_THRESHOLDS["B"]``
     and ``["A"]`` hand-typed a second time. Deleting or re-basing the
     constant — which the 2.0.0 deletion intends to do, across 9 live sites —
     would leave this chart drawing a band that no longer exists, with nothing
     red. The 50 was worse than a twin: it is an ORPHAN, matching no grade cut
     in the dict at all (C is 55, D is 40), so the leftmost colour boundary a
     CDE saw corresponded to nothing this package defines.

  2. THE WORD. "Competitive (70)" is a claim about how the CDFI Fund ranks
     applications, drawn as a dashed reference line on a chart of six
     sub-scores. The Fund publishes no readiness score, no weighting and no
     grade — this package's own Limitation 7 says so — so there is no federal
     referent for a competitiveness bar on that axis. Same shape as the false
     attribution T2 removed from ``schema.py``, rendered to a CDE rather than
     buried in a comment.

WHY A SOURCE SCAN AND NOT A RENDER. This page is a Streamlit script: importing
it executes it, and the chart is a matplotlib figure inside a ``with tabs[0]``
block that needs a full analysis run and a live ``st`` context. The property
asserted here — "the literal is not typed here, the constant is read here" — is
a property OF THE SOURCE, and reading the source is the direct way to ask it.
``tests/test_streamlit_page_imports.py`` covers importability separately.
"""
from __future__ import annotations

import ast
import os
import re

import pytest

from nmtcapp.data.schema import GRADE_THRESHOLDS

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PAGE = os.path.join(_REPO_ROOT, "streamlit_app", "pages", "1_Pipeline_Analyzer.py")


def _page_source() -> str:
    if not os.path.isfile(_PAGE):
        pytest.skip(
            "streamlit_app/pages/1_Pipeline_Analyzer.py is not present — this "
            "is an installed tree, not a checkout. This gate asks a question "
            "about the repository's source."
        )
    with open(_PAGE, encoding="utf-8") as handle:
        return handle.read()


def _string_literals(tree) -> list:
    """Every string a reader sees as ONE unit, f-strings reassembled.

    AN F-STRING IS NOT ONE CONSTANT. ``f"...cut ({_B:.0f})\nnot a CDFI Fund
    threshold"`` parses to a JoinedStr whose Constant parts are split at the
    interpolation, so a scan keyed on either half finds a fragment. The first
    draft of this module asserted the provenance clause and failed against the
    correct label for exactly that reason -- the same defect
    tests/test_fund_attribution_source._string_units was written to fix.
    """
    consumed = set()
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            parts = []
            for value in node.values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    consumed.add(id(value))
                    parts.append(value.value)
                else:
                    parts.append("0")
            out.append((("".join(parts)), node.lineno))
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and id(node) not in consumed):
            out.append((node.value, node.lineno))
    return out


def _readiness_chart_block_lines(source: str) -> tuple:
    """(first, last) 1-indexed line numbers of the readiness-chart block."""
    block = _readiness_chart_block(source)
    start = source[:source.index(block)].count("\n") + 1
    return start, start + block.count("\n")


def _readiness_chart_block(source: str) -> str:
    """The readiness-breakdown block only, so an unrelated 70 cannot satisfy
    or trip this gate.

    Delimited by the two markers that bound it in the file. Both are asserted
    present, so a rename fails loudly here instead of silently narrowing the
    scanned region to nothing — the vacuity shape this package keeps finding.
    """
    start_marker = "**Readiness score breakdown**"
    end_marker = "# TAB 1 — Distress"
    assert start_marker in source, (
        "the readiness-breakdown block's opening marker is gone; this gate no "
        "longer knows which region to read."
    )
    assert end_marker in source, (
        "the readiness-breakdown block's closing marker is gone; this gate "
        "would read to end-of-file."
    )
    block = source[source.index(start_marker):source.index(end_marker)]
    assert len(block) > 800, f"scanned block is {len(block)} chars — too small"
    return block


# ---------------------------------------------------------------------------
# The duplication
# ---------------------------------------------------------------------------

def test_the_chart_reads_grade_thresholds_rather_than_re_typing_them():
    """The constant must be IMPORTED and READ by the block that draws it."""
    source = _page_source()
    assert "GRADE_THRESHOLDS" in source, (
        "1_Pipeline_Analyzer.py does not import GRADE_THRESHOLDS. The colour "
        "ladder and the reference line are drawn from its values; typing them "
        "again is the L-3 duplication this module exists to forbid."
    )
    block = _readiness_chart_block(source)
    reads = block.count("GRADE_THRESHOLDS[")
    assert reads >= 3, (
        f"the readiness chart block reads GRADE_THRESHOLDS {reads} time(s). "
        "The colour ladder has three cut points (A, B, C) and every one of "
        "them must come from the constant."
    )


@pytest.mark.parametrize(
    "value", sorted({int(v) for v in GRADE_THRESHOLDS.values()})
)
def test_no_grade_threshold_is_typed_as_a_literal_in_the_chart_block(value):
    """A live grade cut may not appear as a bare number in this block.

    Parsed with ``ast`` rather than grepped, so the digits inside the
    explanatory comments — which QUOTE the ladder they removed, exactly as the
    FIX-3 notes do elsewhere — cannot trip it. A comment is not a node.

    THIS IS THE ASSERTION THAT GOES RED ON A REVERSION. Restoring
    ``if score < 70: return ACCENT`` puts ast.Constant(70) back in the block
    and fails the [70] case.
    """
    source = _page_source()
    first, last = _readiness_chart_block_lines(source)
    # THE WHOLE FILE IS PARSED AND THE NODES ARE FILTERED BY LINE, rather than
    # re-indenting the fragment and parsing it alone. The fragment approach
    # raised SyntaxError and the except-clause skipped -- a gate that goes
    # green by not running, which is the vacuity shape this package keeps
    # finding in its own suite.
    tree = ast.parse(source)
    literals = [
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
        and first <= node.lineno <= last
    ]
    assert literals, (
        "no numeric literal at all was found in the readiness-chart block. "
        "The line range is wrong and this gate is reading nothing."
    )
    assert value not in literals, (
        f"{value} is a live GRADE_THRESHOLDS value and it is typed as a "
        "literal inside the readiness-chart block. Read the constant instead: "
        "the 2.0.0 deletion removes GRADE_THRESHOLDS across 9 live sites, and "
        "a hand-typed twin here would leave this chart drawing a band that no "
        "longer exists with nothing red.\n\n"
        f"Numeric literals found in the block: {sorted(set(literals))}"
    )


def test_the_orphan_fifty_is_gone():
    """50 was never a grade cut, and the ladder's leftmost boundary used it.

    GRADE_THRESHOLDS's lowest two cuts are C=55 and D=40. The old ladder's
    ``if score < 50`` therefore drew a colour boundary that corresponded to no
    band this package defines — not a stale twin, a number from nowhere.
    """
    assert 50.0 not in GRADE_THRESHOLDS.values(), (
        "50 is now a grade threshold, so this test's premise has changed. "
        "Re-read it rather than deleting it."
    )
    block = _readiness_chart_block(_page_source())
    code = "\n".join(
        line for line in block.splitlines() if not line.strip().startswith("#")
    )
    assert not re.search(r"score\s*<\s*50\b", code), (
        "the orphan 50 is back in the colour ladder. It matches no cut point "
        "in GRADE_THRESHOLDS; if a fourth band is wanted, it needs a constant "
        "and a registry row like every other number this package renders."
    )


# ---------------------------------------------------------------------------
# The word
# ---------------------------------------------------------------------------

def test_the_chart_asserts_nothing_about_competitiveness():
    """"Competitive" on this axis is a Fund claim with no Fund referent.

    Scanned over the STRING LITERALS of the whole page, not the block, because
    the label could migrate to a caption, a tooltip or a legend and still be
    read the same way. Comments are excluded by construction (ast), which
    matters here: the comment that replaced this label quotes the word it
    removed, as this package's notes always do.
    """
    source = _page_source()
    tree = ast.parse(source)
    offenders = []
    for text, lineno in _string_literals(tree):
        if re.search(r"competitiv", text, re.I):
            offenders.append(f"  line {lineno}: {text[:120]!r}")
    assert not offenders, (
        "the Pipeline Analyzer renders a competitiveness claim. The CDFI Fund "
        "publishes no readiness score, no weighting and no grade — this "
        "package's own Limitation 7 — so nothing on the readiness axis has a "
        "federal referent that could make a number 'competitive'.\n\n"
        + "\n".join(offenders)
    )


def test_the_reference_line_says_whose_band_it_is():
    """Withdrawing the false label must not leave an unexplained line.

    A dashed vertical at 70 with no label at all is the mirror defect: the
    reader still infers a bar and now has nothing telling them whose it is.
    The replacement has to name the band AND its provenance.
    """
    source = _page_source()
    tree = ast.parse(source)
    labels = [text for text, _ in _string_literals(tree) if "grade-B cut" in text]
    assert labels, (
        "the reference line no longer carries a label naming the band it "
        "draws. An unlabelled dashed line at 70 is read as a threshold "
        "anyway; the label is the fix, not the deletion."
    )
    assert any("not a CDFI Fund threshold" in text for text in labels), (
        "the reference-line label names the band but not its provenance. It "
        "is this tool's own grade cut and must say so on its face, in the "
        f"label itself:\n  {labels}"
    )
