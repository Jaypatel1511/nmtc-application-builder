"""TWO 1.5.3 LEFTOVERS IN THE DEDUCTION TABLE.

(a) PHRASE INTEGRITY ACROSS A LINE BREAK -- the gate 1.5.3 left able to pass on
    the exact defect it was written to catch.

    ``test_no_component_is_docked_silently`` and
    ``test_a_pipeline_docked_on_geography_is_told_that_it_was`` both assert::

        f"DOCKED {dock:.1f} POINTS" in " ".join(note.split())

    The whitespace tolerance is CORRECT and is kept here: ``readiness_score``
    emits ``{dock:4.1f}`` so a one-digit deduction renders ``DOCKED  5.0
    POINTS``, and what is being asserted is that the figure is STATED, not how
    many spaces precede it.

    What is not correct is that bare ``str.split()`` splits on ALL whitespace,
    newlines included. ``DOCKED 12.4`` ending one line and ``POINTS`` beginning
    the next flattens to the same string and PASSES -- and the column-budget
    gate passes too, both fragments being short. A figure broken across a line
    is the exact defect 1.5.3 existed to fix, and nothing asserted the phrase
    was unbroken.

    So the assertions below run per LINE, collapsing runs of spaces and tabs
    WITHIN a line but never across one. The padding tolerance survives; the
    break does not. And they run on ``wrap_note``'s output as well as on the
    logical note, because ``wrap_note`` is where a break would actually be
    introduced -- the logical note is one line per paragraph and cannot break
    at all, so asserting only on it would be a gate over a surface with no
    exposure.

(b) THE SINGLE-BLOCK WORDING.

    On the DEFAULT SAMPLE PIPELINE -- the first thing any CDE sees -- only ONE
    deduction block renders: nothing docks on a Fund-corresponding row, so that
    block is suppressed. The note nevertheless said

        THE BLOCKS ABOVE ARE NOT THE SAME CURRENCY AND MUST NOT BE TRADED OFF
        AGAINST EACH OTHER

    over one block, and ``TOTAL DEDUCTION 13.4 POINTS`` restated
    ``SUBTOTAL FOR THIS BLOCK: 13.4`` verbatim two lines above it. A disclosure
    sentence that is not true of the artifact it appears in is the defect this
    package keeps auditing out, and this copy of it was on the most-read
    artifact of the six.

    THE SINGLE-BLOCK REPLACEMENT IS NOT SHORTER BY ACCIDENT. What the
    two-block sentence carries that survives with one block -- that a house
    bookkeeping point buys nothing outside this tool -- is kept. What does not
    survive is the comparison between blocks and the measured opposite-
    directions case, because with one block there is no comparison to make.
"""
from __future__ import annotations

import re

import pytest

from nmtcapp.core.application import Application
from nmtcapp.core.cde import CDEProfile
from nmtcapp.core.pipeline import Pipeline
from nmtcapp.validation.readiness_score import (
    READINESS_SCORING_WEIGHTS,
    compute_readiness_score,
    wrap_note,
)


def _flatten_spaces(line: str) -> str:
    """Collapse runs of spaces/tabs WITHIN one line. Never across a newline."""
    return re.sub(r"[ \t]+", " ", line).strip()


def _appears_on_one_line(phrase: str, text: str) -> bool:
    return any(phrase in _flatten_spaces(line) for line in text.split("\n"))


def _sample_score():
    app = Application(cde=CDEProfile.sample(), requested_allocation=65_000_000)
    app.add_pipeline(Pipeline.sample(n=20))
    return app.analyze().readiness_score


def _two_block_score():
    """A pipeline docked on BOTH a Fund-corresponding and a house-only row."""
    pipeline = Pipeline.sample(n=20)
    for project in pipeline:
        project.distress_level = "lic"
        project.state = "IL"
    app = Application(cde=CDEProfile.sample(), requested_allocation=65_000_000)
    app.add_pipeline(pipeline)
    return app.analyze().readiness_score


# ---------------------------------------------------------------------------
# (a) phrase integrity
# ---------------------------------------------------------------------------

def test_a_deduction_phrase_is_never_split_across_a_line():
    score = _sample_score()
    docked = {k: v for k, v in score.component_scores.items() if v < 100}
    assert docked, "precondition: something is docked on the sample pipeline"

    note = score.narrative_note
    wrapped = "\n".join(wrap_note(note))
    for key, value in docked.items():
        dock = (100.0 - value) * READINESS_SCORING_WEIGHTS[key]
        phrase = f"DOCKED {dock:.1f} POINTS"
        assert _appears_on_one_line(phrase, note), (
            f"{phrase!r} is not on any single line of the logical note. A "
            "figure broken across a line is the defect 1.5.3 existed to fix, "
            "and the existing gates flatten newlines so they cannot see it."
        )
        assert _appears_on_one_line(phrase, wrapped), (
            f"{phrase!r} is broken across a line by wrap_note. This is the "
            "surface that actually wraps — the CLI column and the Streamlit "
            "st.code block both render this."
        )


def test_the_total_deduction_phrase_is_never_split_across_a_line():
    score = _sample_score()
    total = sum(
        (100.0 - v) * READINESS_SCORING_WEIGHTS[k]
        for k, v in score.component_scores.items() if v < 100
    )
    phrase = f"TOTAL DEDUCTION {total:.1f} POINTS"
    note = score.narrative_note
    assert _appears_on_one_line(phrase, note), phrase
    assert _appears_on_one_line(phrase, "\n".join(wrap_note(note))), (
        f"{phrase!r} is broken across a line by wrap_note."
    )


def test_the_padding_tolerance_survives():
    """The point of collapsing spaces WITHIN a line, asserted directly.

    ``{dock:4.1f}`` renders a one-digit deduction as ``DOCKED  5.0 POINTS``.
    If this ever tightened into the padding the gate would be asserting a
    column width rather than a statement, which is not what it is for.
    """
    assert _flatten_spaces("    DOCKED  5.0 POINTS  [tag]") == (
        "DOCKED 5.0 POINTS [tag]"
    )


# ---------------------------------------------------------------------------
# (b) the single-block wording
# ---------------------------------------------------------------------------

_TWO_BLOCK_ONLY = (
    "THE BLOCKS ABOVE ARE NOT THE SAME CURRENCY",
    "the two blocks can move in OPPOSITE directions",
)


def _block_headings(note: str) -> int:
    return sum(
        1 for line in note.split("\n")
        if line.startswith("ROWS WHOSE UNDERLYING QUANTITY")
        or line.startswith("ROWS THAT ARE HOUSE BOOKKEEPING")
    )


def test_the_sample_pipeline_renders_one_block():
    """Precondition, measured rather than assumed."""
    assert _block_headings(_sample_score().narrative_note) == 1


def test_a_one_block_note_does_not_talk_about_blocks_plural():
    note = _sample_score().narrative_note
    for phrase in _TWO_BLOCK_ONLY:
        assert phrase not in note, (
            f"one deduction block renders and the note still says {phrase!r}. "
            "A disclosure sentence that is not true of the artifact it appears "
            f"in is worse than none.\n\n{note}"
        )


def test_a_one_block_note_does_not_restate_its_own_subtotal():
    note = _sample_score().narrative_note
    subtotals = [l for l in note.split("\n") if "SUBTOTAL FOR THIS BLOCK" in l]
    assert not subtotals, (
        "with one block the subtotal and the total are the same number stated "
        f"twice, two lines apart: {subtotals}. The total stays; the subtotal "
        "exists to be compared with another block's."
    )


def test_a_one_block_note_still_says_the_point_is_not_a_lever():
    """WITHDRAWING THE SENTENCE MUST NOT WITHDRAW WHAT IT CARRIED."""
    note = _sample_score().narrative_note
    assert "changes this tool's headline and nothing else" in note, (
        "the single-block replacement dropped the one claim that survives with "
        f"one block: that a house point buys nothing outside this tool.\n\n{note}"
    )
    assert "NOT A LIST OF THINGS TO FIX" in note.upper(), (
        "the single-block replacement dropped the statement that the table is "
        f"an account rather than a to-do list.\n\n{note}"
    )


def test_a_two_block_note_keeps_the_no_trade_off_sentence():
    """The other direction: the sentence is true and required when it is true."""
    score = _two_block_score()
    note = score.narrative_note
    if _block_headings(note) != 2:
        pytest.skip("this fixture did not produce two deduction blocks")
    for phrase in _TWO_BLOCK_ONLY:
        assert phrase in note, (
            f"two blocks render and the note no longer says {phrase!r}. "
            "Conditionalising must not delete the case it was written for."
        )
    assert note.count("SUBTOTAL FOR THIS BLOCK") == 2, note
