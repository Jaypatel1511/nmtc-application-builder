"""The `nmtcapp analyze` summary, byte-for-byte, in every analyzer state.

WHY THIS GATE EXISTS (1.4.0 proof 2)

Every other rendered surface in this package has a baseline and the CLI had
none. The four documents have ``tests/rendered_baseline/``; the workbook has a
cell-level capture inside it; the Streamlit page has an AST gate over its metric
labels. `nmtcapp analyze` — which is where a CDE reads its distress shares, its
geographic split and its readiness score back BEFORE it ever generates a
document — could be changed in any way at all and no test would notice.

It was measured rather than assumed: the 1.4.0 change to the geographic block
moves 43 lines of this capture, and nothing in the suite at 56573c0 could see
one of them.

WHAT IT PROTECTS THAT NOTHING ELSE DOES. The states, and specifically the
degraded ones. At 56573c0, with the CDFI Fund eligibility dataset unavailable
and not one project verified, this command printed:

    Urban/Rural:     93% / 7%

— a confident two-way split, computed from state names, for a pipeline about
which the tool knew nothing. No test in the tree rendered the summary in that
state, so no test could see it. The ``unavailable`` capture below is that line.

HOW TO REGENERATE, and when you may: ``python -m tests.cli_baseline_capture >
tests/cli_baseline/analyze.txt``. Regenerate ONLY with the diff read and
classified in the CHANGELOG, exactly as tests/rendered_baseline is treated. A
regenerated baseline passes its own gate — that is what a baseline is — so the
review is the control, not the test run.

THE REPLAY FIXTURE IS PART OF THE CONTRACT. ``tests/cli_baseline_replay.json``
holds the real nmtc-mapper answers for the twenty sample addresses, recorded
once with ``python -m tests.cli_baseline_capture --record-replay``. Re-recording
it changes what the baseline is a baseline OF, so it moves with the same
ceremony. It also means this gate needs no network and no CDFI Fund workbook.
"""
from __future__ import annotations

import difflib
import os

import pytest

from tests import cli_baseline_capture as capture

_BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "cli_baseline", "analyze.txt")


@pytest.fixture(scope="module")
def captured() -> str:
    return capture.capture_all()


def test_the_baseline_file_exists_and_is_not_empty():
    """A missing or truncated baseline would make every check below vacuous."""
    assert os.path.exists(_BASELINE), (
        f"{_BASELINE} is missing. Regenerate with:\n\n"
        "    python -m tests.cli_baseline_capture > tests/cli_baseline/analyze.txt"
    )
    with open(_BASELINE, encoding="utf-8") as fh:
        text = fh.read()
    assert len(text) > 5_000, f"baseline is {len(text)} bytes — truncated?"
    for state in capture.STATES:
        assert f"@@ STATE: {state}" in text, (
            f"the baseline has no capture for the {state!r} analyzer state"
        )


def test_the_analyze_summary_matches_the_baseline(captured):
    """Byte-for-byte, across all five states."""
    with open(_BASELINE, encoding="utf-8") as fh:
        expected = fh.read()

    if captured != expected:
        diff = "\n".join(difflib.unified_diff(
            expected.splitlines(), captured.splitlines(),
            fromfile="tests/cli_baseline/analyze.txt", tofile="captured",
            lineterm="", n=2,
        ))
        pytest.fail(
            "`nmtcapp analyze` output moved.\n\n"
            "This is a RENDERED SURFACE — a CDE reads these figures off the "
            "screen and types them into a form. Classify every changed line "
            "before regenerating, the way tests/rendered_baseline is "
            "treated.\n\n" + diff[:12_000]
        )


def test_the_degraded_states_do_not_report_a_determined_split(captured):
    """The defect this whole round is about, asserted as a rule.

    A baseline catches a change; it does not say which changes are wrong. This
    one does: in ``unavailable`` NOTHING was verified, so the non-metropolitan
    and metropolitan shares must both be 0% and every dollar must sit in the
    third bucket. At 56573c0 this state printed "93% / 7%".
    """
    block = captured.split("@@ STATE: unavailable")[1].split("@@ STATE:")[0]
    assert "Non-metro:       0%" in block, (
        "the unavailable state reports a non-zero non-metropolitan share "
        "while no project was verified:\n" + block[:2000]
    )
    assert "Metropolitan:    0%" in block, (
        "the unavailable state reports a non-zero METROPOLITAN share while no "
        "project was verified. That is the exact defect 1.4.0 R2 removed: the "
        "old metric derived 'urban' as the complement of a twelve-state list, "
        "so an entirely unverified pipeline rendered as 93% urban."
    )
    assert "Not determined:  100%" in block, (
        "the unavailable state does not put every dollar in the undetermined "
        "bucket:\n" + block[:2000]
    )


def test_no_state_reports_shares_that_do_not_account_for_every_dollar(captured):
    """Across every state with QEI, the three shares must sum to 100%.

    Rounding is to whole percents at the render, so the sum is checked with a
    1-point tolerance. What this rules out is a slice going missing — which is
    how the two-way split hid unverified dollars for four releases.
    """
    import re

    pattern = re.compile(
        r"Non-metro:\s+(\d+)%.*?\n\s*Metropolitan:\s+(\d+)%.*?"
        r"\n\s*Not determined:\s+(\d+)%", re.S)
    blocks = [b for b in captured.split("@@ STATE: ")[1:]]
    seen = 0
    for block in blocks:
        name = block.split("\n", 1)[0]
        for non_metro, metro, undet in pattern.findall(block):
            seen += 1
            total = int(non_metro) + int(metro) + int(undet)
            assert abs(total - 100) <= 1, (
                f"in state {name!r} the three county-status shares are "
                f"{non_metro}/{metro}/{undet} and sum to {total}%, not 100%. "
                "Some pipeline QEI is in no bucket at all."
            )
    assert seen >= 4, (
        f"only found {seen} county-status blocks to check — the regex no "
        "longer matches the rendered summary and this gate is vacuous"
    )
