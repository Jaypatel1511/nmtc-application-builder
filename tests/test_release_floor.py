"""release.yml's FLOOR is a hand-typed count inside a gate. This re-derives it.

WHY

The sdist job asserts that the tarball's suite actually EXECUTED tests, rather
than shipping every module and deselecting the lot. The threshold is a shell
variable:

    FLOOR=520

and it has been stale FIVE times in one release cycle: ``FLOOR=125``; ``440``
carried forward from 1.2.0 after the suite grew; ``133`` hand-typed in three
separate places; ``470`` derived from ``954 / -11 / 943``; and ``500``, which
1.3.0 re-derived to 520. Every one of them was WRONG IN THE SAFE DIRECTION,
which is the problem: a floor that is too low never fails, so nothing ever
tells you it is stale. It sits in the file looking like evidence.

FIX-2 makes it six, and the sixth is a new shape: **520 was right and the
measurement recorded for it was not.** The comment beside it read "1,068
collected, 11 skipped, 1,057 executed" -- a run taken from inside the unpacked
tarball, which release.yml's own comment forbids, and which un-skips nine
checks by putting the tarball's source tree on sys.path. The job's real
invocation skipped eighteen there, and twenty here. A digit that is
stale gets remeasured; a
derivation that is merely plausible gets copied forward, so this is the worse
half of the pattern rather than a footnote to it. FLOOR was 530 there, derived
from 1,096 collected and 20 skipped, identically on 3.9.25 and 3.12.13.

1.3.1 MAKES IT SEVEN, AND THIS TEST IS WHAT FOUND IT. The round added 47 tests
and went red on ``FLOOR=530`` before anything in release.yml was touched --
the first stale floor in this file's history caught by a check rather than by
somebody re-reading the comment beside it. FLOOR became 560, derived from
1,143 collected and 23 skipped, identically on 3.9.25 and 3.12.13.

1.3.1's FIX ROUND RE-DERIVED IT AND IT DID NOT MOVE. That round added six
tests (three gates for R1, one for R5, and two for the widened test-count
gate), taking the sdist collection to 1,150 under ``-m "not wheel"`` with 25
skipped -- 1,125 executed, half of which is 562, rounded down to 560. Measured
identically on 3.9.25 and 3.12.13: both 1,125 passed / 25 skipped / 1
deselected. The two new skips are this round's own and are the same
environment class as the other twenty-three: test_docs_refusal_claims' call-site
sweep reads nmtcapp/, and test_test_count_claims' CONTRIBUTING.md site is a
surface the job ships but does not copy out of the tarball.

(The "3.9.12" written here before was a typo for 3.9.25 -- no 3.9.12 was ever
run. A hand-typed coordinate in the paragraph recording a re-derivation, which
is the class R3 of that round is about.)

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
#: TIGHTENED FROM 40 TO 20 IN 1.3.0 B1, then RE-DERIVED TO 24 IN FIX-2 -- and
#: the interesting part is that 20 was tightened onto a measurement that had
#: been taken the wrong way.
#:
#: 1.3.0 justified 20 as "1.8x the measurement", against a measured 11. That 11
#: came from running the suite INSIDE the unpacked tarball, which release.yml's
#: own comment forbids: doing so puts the tarball's source tree on sys.path and
#: un-skips every check that asks whether nmtcapp/ sits beside tests/. Run as
#: the job actually runs it -- from a directory holding only the tarball's
#: tests/ and streamlit_app/ -- ff49064 skips EIGHTEEN, and this tree skips
#: TWENTY. So the ratio was never 1.8x. It was 1.11x at ff49064 and 1.00x
#: here: a ceiling exactly equal to the thing it is supposed to bound.
#:
#: A RATIO WAS THE WRONG WAY TO PICK IT, which is why this note no longer
#: quotes one. The ceiling only changes anything when it crosses a rounding
#: boundary. With 1,096 collected, the lower bound is
#:
#:     ((1096 - MAX_SDIST_SKIPS) // 2) // 10 * 10
#:
#: which returns 530 for every ceiling from 17 to 36 and drops to 520 at 37.
#: Combined with the measured 20 -- a ceiling below its own measurement is not
#: a ceiling -- the live range is [20, 36]. At 37 it starts admitting a floor
#: no measurement of this tree produces, which is what 40 was doing and what
#: made it an abstention rather than a ceiling.
#:
#: RE-DERIVED TO 28 IN 1.3.1, AND 24 WAS ONE SKIP FROM BEING WRONG. The sdist
#: skipped 20 at FIX-2 and skips 23 now, so the ceiling had a single skip of
#: headroom left -- and a ceiling that is about to be crossed by its own
#: measurement stops bounding anything the moment it is.
#:
#: The arithmetic that picks it, restated for this tree. With 1,150 collected
#: the lower bound is
#:
#:     ((1150 - MAX_SDIST_SKIPS) // 2) // 10 * 10
#:
#: which returns 560 for every ceiling up to 30 and drops to 550 at 31. A
#: ceiling below its own measurement is not a ceiling, and the measurement is
#: now 25, so the live range is [25, 30]. At 31 the band starts admitting a
#: floor no measurement of this tree produces, which is what 40 was doing
#: before 1.3.0 and what made it an abstention rather than a ceiling.
#:
#: 28 SITS THREE SKIPS ABOVE THE MEASUREMENT AND TWO BELOW THE SLACK POINT,
#: and that is tighter than it has been. It was five above and sixteen below
#: when it was chosen; this round's two new environment skips took three of
#: that headroom and a larger collection took the rest. It is still a ceiling
#: -- above its own measurement, below the point the band goes slack -- but
#: the next environment skip puts it one from the edge. Re-derive it then;
#: do not widen it to buy room.
#:
#: What skips in the tarball and why -- all twenty-five are environment skips
#: and each names its own reason (the two added in 1.3.1's fix round are
#: test_docs_refusal_claims' guard-call-site sweep, which reads nmtcapp/, and
#: test_test_count_claims' CONTRIBUTING.md claim site, which the job ships but
#: does not copy out): tests needing a git checkout (5, one of them
#: new in 1.3.1: test_the_changelogs_baseline_class_table_adds_up), the
#: constant SWEEPS and the CHANGELOG derivations in test_pinned_constants that
#: read the package SOURCE where this job deliberately has none (9), the docs
#: hooks and docs scans in test_121_financial_tables and
#: test_fund_attribution_source because MANIFEST.in prunes docs/ (4), three
#: that ask about .github/workflows/, which MANIFEST.in does not ship (this
#: module's own two and test_ci_fetches_enough_history_to_answer_this_gate),
#: and two new in 1.3.1 -- test_truncated_lists' F1 sweep and its
#: ruled-exception check, which read nmtcapp/ and streamlit_app/ where this
#: job puts neither beside tests/.
#:
#: If the skip count ever approaches this, the right response is to ask why the
#: sdist stopped being able to answer its own suite's questions -- not to raise
#: the ceiling.
#: RE-DERIVED TO 40 IN 1.5.0, AND 28 HAD BEEN OVERTAKEN BY ITS OWN
#: MEASUREMENT. The sdist now skips THIRTY-SIX -- a ceiling below the thing it
#: bounds is not a ceiling, which is the sentence the 1.3.1 note wrote about
#: 24 and which came true here.
#:
#: The arithmetic, restated for this tree. With 1,230 collected the lower bound
#: is
#:
#:     ((1230 - MAX_SDIST_SKIPS) // 2) // 10 * 10
#:
#: which returns 590 for every ceiling up to 50 and drops to 580 at 51. The
#: measurement is 37, so the live range is [37, 50] and 40 sits THREE skips
#: above its own measurement and ELEVEN below the slack point.
#:
#: WHY THE COUNT JUMPED 25 -> 37. Eleven are the same environment class
#: already enumerated: 1.5.0 adds seven test modules, several of which sweep
#: nmtcapp/ or docs/, and neither tree sits beside tests/ in the job's
#: directory. THE TWELFTH IS A NEW KIND and is worth naming rather than absorbing:
#: tests/test_round_provenance.py's live cdfifund.gov check is marked
#: `network` and skips in EVERY environment, checkout included, by the hook in
#: tests/conftest.py. It is the first skip in this package that is not about
#: the environment at all -- it is opt-in by design, so CI never depends on a
#: federal website being up.
#:
#: 1.5.0 ALSO GAVE THIS CEILING A MEASUREMENT IT CAN FAIL AGAINST, which it
#: never had: tests/test_small_claims.py::test_max_sdist_skips_is_measured_against_something
#: bounds it by the number of test modules structurally capable of skipping in
#: an sdist. Until then nothing in the suite compared this number to anything,
#: and its own comment ("if the skip count ever approaches this...") described
#: a watch nobody was keeping.
MAX_SDIST_SKIPS = 40

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
