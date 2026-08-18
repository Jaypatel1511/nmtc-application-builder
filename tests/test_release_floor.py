"""release.yml's FLOOR is a hand-typed count inside a gate. This re-derives it.

WHY

The sdist job asserts that the tarball's suite actually EXECUTED tests, rather
than shipping every module and deselecting the lot. The threshold is a shell
variable:

    FLOOR=520

and it has been stale FIVE times in one release cycle: ``FLOOR=125``; ``440``
carried forward from 1.2.0 after the suite grew; ``133`` hand-typed in three
separate places; ``470`` derived from ``954 / -11 / 943``; and ``500``, which
1.3.0 re-derived to 520 from a fresh sdist — 1,068 collected, 11 skipped,
1,057 executed, identically on 3.9.25 and 3.12.13. Every one of them was WRONG
IN THE SAFE DIRECTION, which is the problem: a floor that is too low never
fails, so nothing ever tells you it is stale. It sits in the file looking like
evidence.

MAX_SDIST_SKIPS below is the same shape one layer in, and 1.3.0 tightened it
for the same reason.

Deriving it inside the workflow does not work, and that is worth stating rather
than leaving for the next person to rediscover. The floor exists to catch a
marker change or an ``-m`` expression that deselects the suite; a threshold
computed from the same deselected run moves down with it and can never fail.
The reference count has to come from somewhere the deselection cannot reach.
That somewhere is here — a fresh collection, in CI, from the checkout.

WHAT THIS ASSERTS

The derivation rule release.yml states in its own comment: half of what the
sdist genuinely runs, rounded down to a multiple of ten. This test recomputes
both ends of that from a live collection and requires FLOOR to sit between
them. Grow the suite without re-deriving the floor and the lower bound rises
past it, and this fails — which is the whole point.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW = os.path.join(_REPO_ROOT, ".github", "workflows", "release.yml")

#: The job's own marker expression. The reference collection has to use it too,
#: or the two numbers are not measuring the same suite.
MARKER_EXPR = "not wheel"

#: Deliberate sdist-only skips, as a CEILING rather than as today's count.
#:
#: It is a ceiling and not the measurement because this test runs from a
#: CHECKOUT, where none of these skip, so it cannot observe the real number.
#: Widening the band by the ceiling is the honest way to say that.
#:
#: TIGHTENED FROM 40 TO 20 IN 1.3.0 B1, because 40 was not a ceiling, it was an
#: abstention. Measured against a fresh sdist, built from a clean clone and run
#: with the release job's exact invocation: ELEVEN skips, identically on 3.9.25
#: and 3.12.13. A ceiling of 40 against a measured 11 is 3.6x, and it widened
#: this test's band from [520, 534] to [510, 534] — which is to say it admitted
#: a FLOOR of 510 that no measurement of this tree produces. That is a stale
#: count wearing the opposite mask: wrong in the safe direction, so the gate
#: never says so. Same defect as FLOOR itself, one layer in.
#:
#: 20 is 1.8x the measurement. It leaves room for nine more environment-driven
#: skips before the band moves, and the suite would have to grow by about
#: twenty tests before FLOOR=520 falls out of the band — at which point the
#: floor IS stale and re-deriving it is the correct response, which is the
#: behaviour this file exists to force.
#:
#: What skips in the tarball and why: tests needing a git checkout
#: (test_no_committed_generated_artifacts), the constant SWEEPS in
#: test_pinned_constants that read the package SOURCE where the job has no
#: source tree in the working directory, and the docs hooks and
#: docs-withdrawal scans in test_121_financial_tables, because MANIFEST.in
#: prunes docs/.
#:
#: If the skip count ever approaches this, the right response is to ask why the
#: sdist stopped being able to answer its own suite's questions — not to raise
#: the ceiling.
MAX_SDIST_SKIPS = 20

_FLOOR_RE = re.compile(r"^\s*FLOOR=(\d+)\s*$", re.MULTILINE)
_COLLECTED_RE = re.compile(r"(\d+)(?:/\d+)? tests? collected")


def _floor_to_ten(n: int) -> int:
    return (n // 10) * 10


@pytest.fixture(scope="module")
def declared_floor() -> int:
    if not os.path.exists(WORKFLOW):
        pytest.skip(
            ".github/workflows/release.yml is absent (this is an unpacked "
            "sdist or an installed tree, not a checkout). MANIFEST.in does not "
            "ship the workflows, and this gate asks a question about the "
            "repository rather than about the tarball."
        )
    with open(WORKFLOW, encoding="utf-8") as fh:
        text = fh.read()
    matches = _FLOOR_RE.findall(text)
    assert len(matches) == 1, (
        f"expected exactly one 'FLOOR=<n>' assignment in release.yml, found "
        f"{len(matches)}: {matches}. Two assignments is the hazard "
        "benchmark_thresholds.DEEP_DISTRESS_MIN_PCT already demonstrated — the "
        "second silently wins and the pin stays green over the first."
    )
    return int(matches[0])


@pytest.fixture(scope="module")
def collected_count() -> int:
    """A fresh collection of the same suite the sdist job runs.

    A subprocess rather than this session's own item list: this session may
    itself be a filtered run (``pytest tests/test_release_floor.py``), and
    deriving the reference from a filtered run is the same class of error the
    floor exists to catch.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "--collect-only", "-q",
         "-p", "no:randomly", "-p", "no:cacheprovider",
         "-m", MARKER_EXPR, "--strict-markers"],
        cwd=_REPO_ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, (
        "the reference collection failed, so this gate cannot answer its "
        f"question:\n{proc.stdout[-3000:]}\n{proc.stderr[-2000:]}"
    )
    matches = _COLLECTED_RE.findall(proc.stdout)
    assert matches, (
        "could not read a collected count out of pytest's own summary line; "
        f"the tail of its output was:\n{proc.stdout[-1500:]}"
    )
    count = int(matches[-1])
    assert count > 500, (
        f"the reference collection found only {count} tests — it is not "
        "collecting the whole suite, and every bound below would be wrong"
    )
    return count


def test_release_floor_is_derived_from_the_current_suite(
    declared_floor, collected_count
):
    """FLOOR must still be half of what the sdist runs, rounded down to ten.

    Upper bound: the sdist can never execute more than it collects, so half the
    collected count is the largest defensible floor.

    Lower bound: the sdist executes ``collected - skips``; with the skip count
    bounded above, half of that rounded down to ten is the smallest floor the
    stated rule can produce. A floor beneath it is stale, not conservative.
    """
    upper = collected_count // 2
    lower = _floor_to_ten((collected_count - MAX_SDIST_SKIPS) // 2)
    assert lower <= declared_floor <= upper, (
        f"release.yml carries FLOOR={declared_floor}, but the suite now "
        f"collects {collected_count} tests under -m {MARKER_EXPR!r}.\n\n"
        f"The rule release.yml states is half of what the sdist genuinely "
        f"runs, rounded down to a multiple of ten. That puts the floor between "
        f"{lower} and {upper} today.\n\n"
        "Re-derive it: build the sdist, run the job's exact invocation from a "
        "directory containing only what the tarball shipped, and take "
        "(total - skipped) // 2 rounded down to ten. Do not nudge this test's "
        "band to accommodate a number nobody re-measured — that is how FLOOR "
        "got to 440, then 470, while the suite grew underneath it."
    )


def test_release_floor_is_a_round_number(declared_floor):
    """The stated rule ends in 'rounded down to a round number'."""
    assert declared_floor % 10 == 0, (
        f"FLOOR={declared_floor} is not a multiple of ten. release.yml's own "
        "derivation rounds down to one, and a floor that looks precise invites "
        "the reader to believe it was measured to that precision."
    )
