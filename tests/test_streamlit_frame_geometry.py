"""No rendered line on a Streamlit page may fall outside the block that holds it.

THE DEFECT THIS GATE EXISTS FOR (1.5.3 T1/T2)
=============================================

1.5.2's F2 put an honest, sourced, two-currency deduction table on the Pipeline
Analyzer -- the surface that had rendered the readiness composite four ways and
carried no disclosure at all. It shipped, it is live, and it is CUT OFF AT THE
RIGHT EDGE.

``streamlit_app/pages/1_Pipeline_Analyzer.py`` renders the one statement of the
withdrawal with::

    st.code(rs.narrative_note, language=None)

That is the LOGICAL note -- unwrapped paragraphs -- handed straight to a
block that will not reflow it.

``st.code`` emits ``<pre><code>`` carrying ``white-space: pre`` and
``overflow-x: auto``. MEASURED IN THE BROWSER against the deployed app on
2026-08-22 (nmtc-application-builder.streamlit.app/Pipeline_Analyzer, Chrome,
1512 px window):

    font                "Source Code Pro", monospace at 14px
    character advance   8.4 px
    block client width  1052 px   ->  125 characters visible
    block scroll width  6038 px   ->  5.7x wider than the box it sits in
    longest line        715 characters

    Of the 9 prose lines in that render, SEVEN exceed the visible column.
    The clauses that fall off the edge are the load-bearing ones: what was
    withdrawn, why, and the no-trade-off rule. The text is reachable by
    scrolling the block sideways. Essentially nobody will.

``white-space: pre`` DOES NOT WRAP AT ANY VIEWPORT. This was checked rather
than assumed: the block scrolls, it never reflows, so the defect is not a
narrow-window artifact and widening the browser does not fix it.

WHY EVERY EXISTING GATE MISSED IT
=================================

``tests/test_render_frame_geometry.py`` is this package's frame-geometry gate
and its rule is already the right one -- "no rendered text may fall outside the
frame that is supposed to hold it". It closes PDF by measuring the content
stream, rules Word by asserting nothing pins a column width, and rules Markdown
explicitly as having no frame to fall out of.

IT NAMES THREE SURFACES. There are four. ``streamlit_app/`` produces no filed
artifact, so it sat outside the sweep -- the identical reasoning that put the
distress-share defect on this same page in 1.3.0, and the identical shape as
1.5.2's F2: THE SURFACE EXISTS, THE GATE'S SURFACE LIST DOES NOT INCLUDE IT.

WHERE THE FIX LIVES, AND WHY NOT AT SOURCE
==========================================

1.5.3 lays the note out AT THE CALL SITE, through the shared
``readiness_score.wrap_note`` that ``nmtcapp analyze`` already used -- it does
NOT pre-wrap the note inside ``narrative_withdrawal_note``. Pre-wrapping was
tried first and reverted; ``wrap_note``'s own docstring records the two things
that broke, both found by execution. The consequence for this module is
``test_the_page_lays_the_note_out_before_it_renders_it``: measuring a layout
the page does not apply would be green on the defect it exists for.

WHY THIS IS A SIBLING FILE AND NOT A SECTION OF THE PDF ONE
===========================================================

``test_render_frame_geometry.py`` opens with module-level
``pytest.importorskip("reportlab")`` and ``importorskip("pypdf")``. A Streamlit
assertion parked in that module SKIPS SILENTLY wherever those two are absent,
and a gate that stops covering a surface without saying so is the failure this
package keeps paying for. Nothing here needs reportlab, so nothing here should
be able to skip with it.

THE SCOPE LIMIT, DECLARED (and it is the whole reason this docstring is long)
============================================================================

THIS GATE COUNTS CHARACTERS. IT DOES NOT MEASURE RENDERED WIDTH. A PDF frame is
a measured box in points and the PDF gate really does measure it. A browser
container is not: its width depends on the viewport, the sidebar state, the
user's zoom and the font actually resolved, none of which exist in a test
process. 1052 px / 8.4 px = 125 columns is a measurement of ONE window on ONE
machine, and hard-coding it would be an approximation dressed as a bound --
which is how this package's proximity gate spent a release satisfiable from 69
characters away.

So the bound asserted here is a CHARACTER COUNT, and it is DERIVED FROM WHAT
THE PACKAGE ALREADY SHIPS rather than chosen:

    ``readiness_score.wrap_note``    wraps prose to NOTE_PROSE_WIDTH=76; the
                                     CLI adds two spaces  ->  78 columns.
    ``narrative_withdrawal_note``    wraps each FUND note to width=64 under a
                                     14-space continuation indent  ->  78.

Both established columns land on 78, so 78 is the note's column and this gate
asserts it. Both derivations are re-checked below (see
``test_the_column_is_derived_from_the_shipped_wrap_and_not_typed_here``) so the
bound cannot drift away from the code that sets it.

WHAT 78 COLUMNS BUYS, STATED HONESTLY: it fits every viewport at which the
block renders at all, with room to spare at the 125 measured above. It is a
SUFFICIENT bound, not a necessary one -- a line of 100 characters would also
have been visible in that browser. This gate prefers the shipped column to a
measured one precisely because the measured one is not portable.

THE ROWS ARE IN THE BUDGET TOO, AND THE RATCHET THAT EXEMPTED THEM IS GONE
=========================================================================

The first 1.5.3 commit wrapped the prose and left the pre-formatted deduction
rows on a RATCHET at 124 columns -- "they may not get wider". THAT WAS A BOUND
ABOVE THE BUDGET, so this module certified the exact lines that clip.

Retired after OBSERVING the app in Chrome rather than deriving it:

    1512 px window, root -> sidebar nav   block 1052 px   125 cols   fits
    1512 px window, DIRECT LINK to page   block  704 px    83 cols   CLIPS
    1180 px window                        block  720 px    85 cols   CLIPS

``layout="wide"`` is set by the ENTRYPOINT script, so a direct link or bookmark
straight to the Pipeline Analyzer renders in the centred 704 px column. The
narrow case is not an unusual laptop -- it is what a shared link does. At 85
columns the reader kept ``DOCKED 12.4 POINTS  [sc`` and lost
``hema.IMPACT_BENCHMARKS (HOUSE)]``: the deduction survives, the tag saying it
is this tool's own band does not. That is the worst token on the line to lose.

``wrap_note`` now moves the tag to a ``BASIS:`` continuation at the indent the
``FUND:`` lines already use -- an existing pattern applied, not a table
redesigned -- and the row head is a constant 78 columns. EVERY rendered line is
now held to NOTE_COLUMN. There is no exemption left in this file.

WHAT THIS GATE STILL DOES NOT COVER
===================================

  - MARKDOWN'S COPY OF THE TABLE. ``_withdrawal_markdown`` passes the rows
    through as an indented code block, which does not reflow either. Markdown
    is ruled frameless by ``test_render_frame_geometry`` and is not measured
    here, so the long-row form still exists in a generated .md. Recorded.
  - THE RENDERED WIDTH ITSELF, per the scope limit above.
  - WHETHER THE DEPLOYED APP SHOWS THE FIX. Nothing here reads production.
"""
from __future__ import annotations

import ast
import pathlib
import textwrap

import pytest

from nmtcapp.data.schema import READINESS_SCORING_WEIGHTS
from nmtcapp.validation.readiness_score import (
    narrative_withdrawal_note,
    wrap_note,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
STREAMLIT_DIR = REPO_ROOT / "streamlit_app"

# The note's column, derived rather than chosen. See the module docstring;
# ``test_the_column_is_derived_from_the_shipped_wrap_and_not_typed_here``
# re-derives both halves so this constant cannot drift from the code.
NOTE_COLUMN = 78

# THE RATCHET THAT USED TO LIVE HERE IS RETIRED (1.5.3 follow-up).
#
# It recorded the widest pre-formatted deduction row -- 124 columns -- and
# asserted only that the rows did not get WIDER. That is a bound ABOVE the
# 78-column budget the same gate enforces on prose, which meant this module
# CERTIFIED THE EXACT LINES THAT CLIP: at the 83 columns a direct link to the
# page actually renders, a 117-column row loses its basis tag and the ratchet
# stayed green.
#
# There is now ONE bound for every rendered line, prose and pre-formatted
# alike, and it is NOTE_COLUMN. Nothing in this file is exempt from it.


def _worst_case_scores() -> dict:
    """Every component docked, so every deduction row renders.

    The shipped fixtures leave components at 100, which drops their rows
    entirely -- that is how 1.5.1's F2 hid two withdrawn branches from every
    test in the suite. The widest row must be reachable by this gate on
    purpose rather than by luck of the fixture.
    """
    return dict(
        zip(READINESS_SCORING_WEIGHTS.keys(), [72.5, 61.0, 48.3, 83.9, 55.2, 90.1])
    )


def _worst_case_note() -> str:
    """The note as ``narrative_withdrawal_note`` returns it: LOGICAL paragraphs."""
    return narrative_withdrawal_note(_worst_case_scores())


def _rendered_streamlit_note(note: str = None) -> str:
    """The note AS THE PAGE RENDERS IT -- laid out through :func:`wrap_note`.

    THIS IS THE DISTINCTION THE GATE TURNS ON. The note's canonical form is
    unwrapped, because markdown reflows and must keep receiving it whole (see
    ``wrap_note``'s docstring for the two things that broke when the wrap was
    made canonical instead). What ``st.code`` receives is the LAID-OUT form,
    and that is what has a frame, so that is what is measured here.

    Measuring the canonical note instead would report a defect that no longer
    reaches a user; measuring only the page's source would report nothing.
    """
    return "\n".join(wrap_note(_worst_case_note() if note is None else note))


def _split(note: str) -> tuple:
    """Partition a note into (prose, pre-formatted) lines.

    The four-space indent is the same marker ``_wrap_note`` uses to decide
    what it may rewrap, so this gate partitions on exactly the rule the
    renderer partitions on rather than a second copy of the idea.
    """
    prose, preformatted = [], []
    for i, line in enumerate(note.split("\n")):
        if not line.strip():
            continue
        (preformatted if line.startswith("    ") else prose).append((i, line))
    return prose, preformatted


# ---------------------------------------------------------------------------
# The surface list, asserted rather than maintained by hand
# ---------------------------------------------------------------------------

def _st_code_call_sites() -> list:
    """Every ``st.code(...)`` in the Streamlit app, found by AST walk.

    THIS IS THE ANTI-F2 ASSERTION. The reason the deduction table shipped
    clipped is not that anyone measured it wrong -- it is that the surface was
    never on a list. Grepping once and writing the answer into a test makes
    the next ``st.code`` invisible in exactly the same way, so the list is
    recomputed from source on every run.
    """
    sites = []
    for path in sorted(STREAMLIT_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "code"
                and isinstance(func.value, ast.Name)
                and func.value.id == "st"
            ):
                sites.append((path.relative_to(REPO_ROOT).as_posix(), node.lineno))
    return sites


# The ``st.code`` blocks this gate knows how to measure. A site that appears in
# the source and not here fails the test below -- which is the point.
COVERED_ST_CODE_SITES = {
    "streamlit_app/pages/1_Pipeline_Analyzer.py": "rs.narrative_note",
}


def test_every_st_code_block_in_the_app_is_covered_by_this_gate():
    """A new fixed-width block may not appear without this gate learning it.

    1.5.2's F2 was a surface that existed while the gate's surface list did
    not include it. This asserts the list is not maintained by hand: any
    ``st.code`` added to any page fails here until it is either measured by
    this module or explicitly ruled on.
    """
    found = {path for path, _ in _st_code_call_sites()}
    unknown = found - set(COVERED_ST_CODE_SITES)
    assert not unknown, (
        "a Streamlit page renders a fixed-width st.code block this gate does "
        "not measure. st.code never wraps (white-space: pre), so whatever it "
        "renders is clipped at the container edge exactly as the 1.5.2 "
        "deduction table was. Add it to COVERED_ST_CODE_SITES and assert its "
        "width, or rule explicitly that it cannot overflow.\n"
        f"  uncovered: {sorted(unknown)}"
    )
    assert found, (
        "no st.code call was found in streamlit_app/ at all. Either the AST "
        "walk broke or the surface moved; both mean this gate is measuring "
        "nothing and must not be read as green."
    )


def test_the_page_lays_the_note_out_before_it_renders_it():
    """The ``st.code`` argument must pass through ``wrap_note``.

    WITHOUT THIS, EVERY MEASUREMENT IN THIS MODULE IS ABOUT A STRING THE PAGE
    DOES NOT RENDER. The note's canonical form is unwrapped -- markdown needs
    it that way -- so the fix for the Streamlit surface lives at the call site,
    and a gate that measured ``wrap_note(note)`` while the page rendered
    ``rs.narrative_note`` would be green on the exact defect it was built for.

    That is not hypothetical: ``st.code(rs.narrative_note, language=None)`` is
    precisely what shipped in 1.5.2 and what this release changes.

    Asserted structurally (the call's argument mentions ``wrap_note``) rather
    than by executing the page, because importing a Streamlit page runs it.
    SCOPE LIMIT: this proves the layout function is applied, not that its
    result is what reaches the browser unaltered.
    """
    page = REPO_ROOT / "streamlit_app" / "pages" / "1_Pipeline_Analyzer.py"
    tree = ast.parse(page.read_text(encoding="utf-8"), filename=str(page))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "code"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "st"
    ]
    assert calls, "1_Pipeline_Analyzer.py no longer calls st.code at all"
    unwrapped = []
    for call in calls:
        arg_src = ast.dump(call.args[0]) if call.args else ""
        if "wrap_note" not in arg_src:
            unwrapped.append(
                f"  line {call.lineno}: st.code(...) does not lay its argument "
                "out through wrap_note"
            )
    assert not unwrapped, (
        "a Streamlit st.code block renders text that was never laid out. "
        "st.code sets white-space: pre and never wraps, so an unwrapped "
        "715-character paragraph is clipped at the container edge -- the 1.5.2 "
        "defect exactly.\n" + "\n".join(unwrapped)
    )


def test_the_other_streamlit_pages_render_no_unwrapped_fixed_width_text():
    """The sweep of the other three pages, recorded so the negative is not assumed.

    1.5.2's F2 found a second instance the moment its gate widened by one
    notch, so this was checked rather than presumed. Walked for ``st.code``,
    ``st.text``, ``st.json``, ``st.table``, ``st.latex`` and ``st.help`` --
    every Streamlit primitive that renders text at a fixed width without
    reflowing.

    RESULT: only page 1 carries one, and it is the withdrawal note.
    ``st.dataframe`` appears five times and is deliberately NOT in that list:
    it is a scrollable widget that reflows its own columns and is passed a
    container-fitting width at every call site.
    """
    fixed_width_attrs = {"code", "text", "json", "table", "latex", "help"}
    found = []
    for path in sorted(STREAMLIT_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr in fixed_width_attrs
                and isinstance(func.value, ast.Name)
                and func.value.id == "st"
            ):
                found.append(
                    (path.relative_to(REPO_ROOT).as_posix(), func.attr, node.lineno)
                )
    unexpected = [f for f in found if f[0] not in COVERED_ST_CODE_SITES]
    assert not unexpected, (
        "a Streamlit page renders fixed-width text this gate has not ruled "
        "on. Every one of these primitives emits text that does not reflow.\n"
        f"  {unexpected}"
    )


# ---------------------------------------------------------------------------
# The measurement
# ---------------------------------------------------------------------------

def test_no_prose_line_in_the_withdrawal_note_exceeds_the_note_column():
    """THE GATE. Every prose line of the note fits the column the note is laid out in.

    This is the assertion that was red when 1.5.3 opened: the prose paragraphs
    were single lines of up to 715 characters, relying on a soft wrap that
    ``white-space: pre`` never performs.
    """
    prose, _ = _split(_rendered_streamlit_note())
    over = [(i, len(line), line[:60]) for i, line in prose if len(line) > NOTE_COLUMN]
    assert not over, (
        f"{len(over)} prose line(s) of the withdrawal note exceed the note's "
        f"{NOTE_COLUMN}-column layout. st.code renders with white-space: pre "
        "and never wraps, so every character past the container edge is "
        "invisible to a CDE who does not scroll the block sideways -- and the "
        "clauses that fall off are what was withdrawn, why, and the "
        "no-trade-off rule.\n"
        + "\n".join(
            f"  line {i}: {n} cols (>{NOTE_COLUMN})  {t!r}..." for i, n, t in over
        )
    )


def test_the_note_still_fits_the_column_on_a_pipeline_with_nothing_docked():
    """The no-deduction branch is prose end to end and must fit too."""
    note = narrative_withdrawal_note(
        {k: 100.0 for k in READINESS_SCORING_WEIGHTS}
    )
    prose, _ = _split(_rendered_streamlit_note(note))
    over = [(i, len(line)) for i, line in prose if len(line) > NOTE_COLUMN]
    assert not over, (
        "the undocked branch of the withdrawal note overflows the column: "
        f"{over}"
    )


def test_no_preformatted_deduction_row_exceeds_the_note_column_either():
    """The rows are held to the SAME bound as the prose. No exemption.

    WHAT CHANGED AND WHY THE OLD SHAPE WAS WRONG. Through the first 1.5.3
    commit this assertion was a RATCHET at 124 columns -- "the rows may not get
    wider than they are today". A ratchet above the budget is not a bound: it
    certified lines that clip, in the module whose entire subject is lines that
    clip.

    OBSERVED IN CHROME against the app, which is what retired it:

        1512 px window, root -> sidebar nav   block 1052 px   125 cols   fits
        1512 px window, DIRECT LINK to page   block  704 px    83 cols   CLIPS
        1180 px window                        block  720 px    85 cols   CLIPS

    ``layout="wide"`` is set by the entrypoint script, so any direct link or
    bookmark to the Pipeline Analyzer renders in the centred 704 px column.
    That is not an unusual viewport; it is the default for a shared link. At 85
    columns the reader kept ``DOCKED 12.4 POINTS  [sc`` and lost
    ``hema.IMPACT_BENCHMARKS (HOUSE)]``.

    ``wrap_note`` now moves the basis tag onto a BASIS: continuation at the
    same indent the FUND: lines already use, so every line fits 78.
    """
    lines = [
        (i, line)
        for i, line in enumerate(_rendered_streamlit_note().split("\n"))
        if line.strip()
    ]
    assert lines, "the note rendered nothing; this gate measured nothing."
    over = [(i, len(l), l[:64]) for i, l in lines if len(l) > NOTE_COLUMN]
    assert not over, (
        f"{len(over)} rendered line(s) exceed the {NOTE_COLUMN}-column budget. "
        "st.code never wraps, and a direct link to this page renders in an "
        "83-column block, so anything past the bound is invisible without a "
        "sideways scroll -- and on a deduction row the part that falls off is "
        "the tag naming the band as this tool's own.\n"
        + "\n".join(f"  line {i}: {n} cols  {t!r}..." for i, n, t in over)
    )


def test_every_deduction_row_still_carries_an_extractable_basis_tag():
    """The contract ``wrap_note`` relies on to move the tag at all.

    ``_lay_out_deduction_row`` finds the basis tag by its trailing ``  [tag]``
    marker and leaves the line ALONE when there is none. That is the right
    failure mode -- it never corrupts a row it does not understand -- but it
    means a change to the row format in ``narrative_withdrawal_note`` would
    silently stop the split and put the rows back over the budget.

    The width gate above would catch that. This one says WHY, at the line that
    broke, rather than leaving a reader to rediscover the coupling.
    """
    from nmtcapp.validation.readiness_score import _split_basis_tag

    rows = [
        line
        for line in _worst_case_note().split("\n")
        if line.startswith("    ") and "DOCKED" in line
    ]
    assert len(rows) == 6, (
        f"expected six deduction rows on an all-six-docked pipeline, got "
        f"{len(rows)}; this gate is not measuring the table it thinks it is."
    )
    missing = [r for r in rows if _split_basis_tag(r)[1] is None]
    assert not missing, (
        "a deduction row no longer ends in the '  [tag]' marker wrap_note "
        "splits on, so its basis tag can no longer be moved to a "
        "continuation.\n" + "\n".join(f"  {r[:80]!r}" for r in missing)
    )
    # And the tag must survive the move intact -- moving is allowed, breaking
    # a token is not. This is the "jobs-per-$1MM- QEI" rule applied to the tag.
    for row in rows:
        _, tag = _split_basis_tag(row)
        laid_out = _lay_out_row(row)
        assert any(tag in line for line in laid_out), (
            f"the basis tag {tag!r} did not survive layout intact"
        )


def _lay_out_row(row: str) -> list:
    from nmtcapp.validation.readiness_score import _lay_out_deduction_row
    return _lay_out_deduction_row(row, NOTE_COLUMN)


def test_the_column_is_derived_from_the_shipped_wrap_and_not_typed_here():
    """NOTE_COLUMN must keep matching the code that actually lays the note out.

    A bound hand-typed into a gate is the defect this package shipped in 1.5.1
    -- three files agreeing with each other while the subject had moved. Both
    derivations of 78 are recomputed here, so changing either wrap width fails
    this test instead of silently loosening the gate.
    """
    import inspect

    # Derivation 1: the CLI wrap. _wrap_note wraps prose to its default width
    # and prefixes two spaces.
    cli_width = inspect.signature(wrap_note).parameters["width"].default
    assert cli_width + 2 == NOTE_COLUMN, (
        f"wrap_note wraps to {cli_width} and the CLI indents 2, giving "
        f"{cli_width + 2} columns, but NOTE_COLUMN says {NOTE_COLUMN}."
    )

    # Derivation 2: the FUND continuation lines inside the deduction rows.
    src = inspect.getsource(narrative_withdrawal_note)
    assert "textwrap.wrap(fund, width=64" in src, (
        "the FUND note wrap width moved. NOTE_COLUMN is derived from it "
        "(64 + a 14-space continuation indent = 78) and must be re-derived."
    )
    _, preformatted = _split(_rendered_streamlit_note())
    fund_lines = [
        line for _, line in preformatted if line.strip().startswith("FUND:")
    ]
    assert fund_lines, "no FUND line rendered; derivation 2 measured nothing."
    assert max(len(line) for line in fund_lines) <= NOTE_COLUMN


# ---------------------------------------------------------------------------
# The gate's own failure, proved
# ---------------------------------------------------------------------------

def test_the_checker_catches_a_line_lengthened_past_the_column():
    """The checker fires on a line it should fire on, naming file and line.

    Without this, "the width gate is green" could mean the partition never
    handed it a prose line -- which is how ``_split`` returning nothing would
    read as a pass.
    """
    note = _rendered_streamlit_note()
    lines = note.split("\n")
    # Lengthen the first prose line past the column, exactly as an unwrapped
    # paragraph did before 1.5.3.
    target = next(i for i, l in enumerate(lines) if l.strip() and not l.startswith("    "))
    lines[target] = lines[target] + " x" * NOTE_COLUMN
    prose, _ = _split("\n".join(lines))
    over = [(i, len(line)) for i, line in prose if len(line) > NOTE_COLUMN]
    assert over, "the checker did not catch a deliberately over-long prose line"
    assert over[0][0] == target, (
        f"the checker caught a line, but named {over[0][0]} rather than the "
        f"line actually lengthened ({target})"
    )


def test_the_partition_does_not_silently_hand_the_gate_an_empty_list():
    """A pass must mean 'measured and fits', never 'measured nothing'."""
    prose, preformatted = _split(_rendered_streamlit_note())
    assert len(prose) >= 8, (
        f"only {len(prose)} prose lines partitioned out of the note; the gate "
        "above would pass while measuring almost nothing."
    )
    assert len(preformatted) >= 20, (
        f"only {len(preformatted)} pre-formatted lines partitioned out; the "
        "deduction table stopped rendering."
    )
