"""A KEY NAMED ``min_deep_distress`` THAT DOES NOT MEASURE DEEP DISTRESS.

THE DEFECT (1.5.4 T5)

``schema.TARGET_DISTRESS_THRESHOLDS`` has two keys, ``min_deep_distress`` and
``target_deep_distress``. Every one of their four read sites compares them
against ``pct_deep_or_severe`` -- deep and severe COLLAPSED INTO ONE BAND:

    validation/readiness_score.py:249,254     _distress_score, on pct_deep_or_severe
    intelligence/distress_analysis.py:179,180 meets_min/target_threshold, same
    validation/eligibility_check.py:112       on deep+severe QEI, same

The CDFI Fund scores them as TWO SEPARATE sub-scores with distinct bars --
``SEVERE_DISTRESS_MIN_PCT`` 0.85 and ``DEEP_DISTRESS_MIN_PCT`` 0.20 -- and this
package's own win-probability model keeps them separate. Only the readiness
composite collapses them, under a key that names the half it is not measuring.

WHAT THAT PRODUCES, MEASURED. On an all-severe / no-deep pipeline (pct_deep 0.0,
pct_deep_or_severe 1.0):

    readiness    distress_concentration  100.0/100, not docked
    engine       Deep Distress Commitment  0/10, and named as a gating reason

THE PLANNING NOTE FOR THIS ROUND CALLED THAT "a direct factual conflict about
the same quantity". IT IS NOT, AND SAYING SO PRECISELY IS THE FIX. Those two
statements are about DIFFERENT quantities that share a word: one is the share of
QEI in deep-OR-severe tracts, the other is the share in deep tracts alone. Both
are true, simultaneously, on that pipeline. There is nothing to reconcile
between them and no trade-off to price.

What is false is the CONSTANT'S NAME, which tells every future reader that the
readiness band measures deep distress. That is the "files agree with each other
but not with the truth" class, and it is why the fix is a documented semantic
plus a gate rather than a reconciliation of two numbers that do not disagree.

RENAMING IT IS DEFERRED TO 2.0.0. ``TARGET_DISTRESS_THRESHOLDS`` is exported as
``nmtcapp.data.TARGET_DISTRESS_THRESHOLDS`` and its keys are read by four
modules and asserted by name in tests/validation/test_readiness_narrative_
withdrawn.py. Renaming a key in a public dict is a breaking change and a patch
may not make one. It queues behind ``overall_score`` / ``grade`` /
``GRADE_THRESHOLDS``.

SO THE GATE IS BEHAVIOURAL, NOT LEXICAL. A test asserting the docstring says
"pct_deep_or_severe" would be a test that the comment agrees with itself. These
assert that the QUANTITY the band is measured on is the combined share -- by
holding it fixed while moving ``pct_deep`` underneath it, and then moving it.
"""
from __future__ import annotations

import pytest

from nmtcapp.data.schema import TARGET_DISTRESS_THRESHOLDS
from nmtcapp.data import benchmark_thresholds as bt
from nmtcapp.validation.readiness_score import _distress_score


class _Result:
    """The one field ``_distress_score`` reads."""

    def __init__(self, **breakdown):
        self.distress_breakdown = breakdown


#: The quantity the two keys are documented to be measured on. Written here as
#: a string because the assertion below is that the CODE measures it, not that
#: a comment names it.
_MEASURED_ON = "pct_deep_or_severe"


def test_the_band_is_measured_on_the_combined_share_not_on_deep_alone():
    """Move ``pct_deep`` under a fixed combined share: nothing may change."""
    fixed = 0.60
    scores = {
        deep: _distress_score(_Result(pct_deep_or_severe=fixed, pct_deep=deep))
        for deep in (0.0, 0.20, 0.60)
    }
    assert len(set(scores.values())) == 1, (
        "TARGET_DISTRESS_THRESHOLDS['min_deep_distress'] changed the readiness "
        f"distress score when only pct_deep moved: {scores}. The key is "
        f"documented as measured on {_MEASURED_ON}; if that is no longer true, "
        "the documented semantics and the measured quantity have diverged and "
        "the constant's comment is now false."
    )


def test_the_band_does_respond_to_the_combined_share():
    """The other direction: a gate that cannot fail proves nothing.

    Without this, the test above is satisfied by a function that ignores
    distress entirely.
    """
    below = TARGET_DISTRESS_THRESHOLDS["min_deep_distress"] - 0.10
    above = TARGET_DISTRESS_THRESHOLDS["min_deep_distress"] + 0.10
    low = _distress_score(_Result(pct_deep_or_severe=below, pct_deep=0.0))
    high = _distress_score(_Result(pct_deep_or_severe=above, pct_deep=0.0))
    assert high > low, (
        f"the readiness distress score did not rise when {_MEASURED_ON} "
        f"crossed min_deep_distress ({below} -> {above}): {low} -> {high}"
    )


def test_the_house_band_is_not_the_funds_deep_distress_bar():
    """The two must not be allowed to converge silently.

    If ``min_deep_distress`` ever equalled ``DEEP_DISTRESS_MIN_PCT`` a reader
    would take the house band for the Fund's, and the name would stop being
    the only misleading thing about it.
    """
    assert (
        TARGET_DISTRESS_THRESHOLDS["min_deep_distress"]
        != bt.DEEP_DISTRESS_MIN_PCT
    ), (
        "schema.TARGET_DISTRESS_THRESHOLDS['min_deep_distress'] now equals "
        "benchmark_thresholds.DEEP_DISTRESS_MIN_PCT. One is a house screening "
        "band measured on deep-OR-severe QEI; the other is the CDFI Fund's "
        "Deep Distress bar, measured on QLICIs, deep tracts only. Equal values "
        "under a shared word is how a house band gets read as a federal one."
    )


def test_the_fund_keeps_the_two_distress_tiers_separate():
    """The premise the constant's name violates, asserted so it stays true."""
    assert bt.SEVERE_DISTRESS_MIN_PCT != bt.DEEP_DISTRESS_MIN_PCT, (
        "the Fund's severe and deep bars are now the same number, so the "
        "collapse this module documents would no longer be observable."
    )


def test_the_constant_documents_the_quantity_it_is_measured_on():
    """The half a behavioural gate cannot cover: the next reader.

    A future maintainer reads the name before they read the four call sites.
    ``min_deep_distress`` tells them it measures deep distress. The comment
    beside it must say otherwise, in the words the breakdown key uses, so the
    two tests above have something to be a gate ON.
    """
    import inspect
    from nmtcapp.data import schema

    source = inspect.getsource(schema)
    marker = "TARGET_DISTRESS_THRESHOLDS = {"
    head = source[max(0, source.index(marker) - 3000):source.index(marker)]
    assert _MEASURED_ON in head, (
        "the comment above TARGET_DISTRESS_THRESHOLDS does not name "
        f"{_MEASURED_ON}, so nothing tells a reader that a key called "
        "'min_deep_distress' is measured on deep AND severe combined. "
        "tests/test_distress_band_semantics.py asserts the behaviour; this "
        "asserts the reader is told."
    )


@pytest.mark.parametrize("key", ["min_deep_distress", "target_deep_distress"])
def test_both_keys_are_measured_on_the_same_combined_share(key):
    """``target_deep_distress`` is misnamed in exactly the same way."""
    value = TARGET_DISTRESS_THRESHOLDS[key]
    below = _distress_score(_Result(pct_deep_or_severe=value - 0.05, pct_deep=0.0))
    at = _distress_score(_Result(pct_deep_or_severe=value + 0.05, pct_deep=0.0))
    assert at > below, (
        f"{key} does not band on {_MEASURED_ON}: {below} -> {at} across its "
        "own value."
    )
    # And it is NOT banding on pct_deep, which is what its name says.
    same = _distress_score(_Result(pct_deep_or_severe=value + 0.05, pct_deep=0.99))
    assert same == at, (
        f"{key} responded to pct_deep. Its name would then be correct and this "
        "module's premise wrong — re-read the four call sites."
    )
