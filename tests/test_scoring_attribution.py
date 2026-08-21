"""THE SCORING-ATTRIBUTION GATE: a constant that feeds a score must say where it came from.

WHAT THIS CLOSES, AND WHY IT IS THE ROUND'S POINT

Nine metrics were scored against constants citing a publication that
``nmtcapp/data/historical_awards.py``'s OWN HEADER says does not exist. 1.4.0
deleted one of the nine. Eight remained -- two of them three lines above the
deletion, in the same block, touched by the same diff.

That is not eight bugs. It is one class, found nine times, fixed once per
finding. This module is the mechanism that makes the tenth impossible to ship
in silence, and the enumeration it forced was larger than any brief for it had
guessed: SIXTY-NINE top-level constants, not nine.

WHY NO EXISTING GATE REACHED THIS CORPUS

  ``test_pinned_constants``  sweeps ``nmtcapp/data/{schema,benchmark_thresholds}``
                             and nothing else. ``DATA_MODULES`` has never
                             contained ``historical_awards.py``, so its four
                             winner dicts were in no sweep at all -- not
                             pinned, not waived, not seen. Thirty-three
                             constants, invisible by construction.

  its waiver rows            rule Section B's three dicts with "reaches no
                             rendered surface". That is a RENDERING answer to
                             an ATTRIBUTION question. Whether a number is
                             printed and whether anyone knows where it came
                             from are different facts; answering the first has
                             been standing in for asking the second.

  ``test_fund_attribution_source``  keys on an AUTHORITY TOKEN -- "CDFI Fund",
                             "the Fund", "Review Process". ``"std_states":
                             3.8`` names nobody and asserts nothing, so it is
                             invisible there. The defect's whole shape is that
                             it is SILENT.

THE RULE

Every top-level key of every dict in the winner-pattern corpus must carry a row
in ``tests/scoring_attribution.txt``, ``CITED`` with a retrievable document or
``HOUSE`` as this package's own construct. A key with no row FAILS. A row for a
key that no longer exists FAILS -- a stale ruling reads as coverage.

WHAT A HOUSE ROW IS NOT. It is not a licence to keep a number. It is a
DECLARATION THAT NO SOURCE EXISTS, and the standing ruling (1.5.0 S3) is source
it or delete it. Six keys with no consumer were deleted this round rather than
given a row. What survives has a consumer, so removing it moves a figure a CDE
sees; that is the next release's work, and these rows are what make the
candidate list explicit instead of buried in a dict nobody sweeps.

FAILS CLOSED. An empty corpus, an empty registry, a dict that vanished from the
sweep, or a row whose source is blank all error rather than pass.
"""
from __future__ import annotations

import os

import pytest

import nmtcapp.data.benchmark_thresholds as benchmark_thresholds
import nmtcapp.data.historical_awards as historical_awards

REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "scoring_attribution.txt")

KINDS = {"CITED", "HOUSE"}

#: THE CORPUS, named per dict rather than by scanning for "every dict in the
#: module". A module-level scan would silently widen when somebody adds a
#: lookup table that is not a scoring constant, and a gate whose scope drifts
#: is one whose failures stop meaning a fixed thing. A dict listed here that
#: no longer exists FAILS -- see test_the_corpus_is_still_present -- so the
#: list cannot go stale the other way either.
CORPUS = {
    "NMTC_AWARD_ROUNDS": historical_awards,
    "AWARD_SIZE_TIERS": historical_awards,
    "WINNER_DISTRESS_PATTERNS": historical_awards,
    "WINNER_GEOGRAPHIC_PATTERNS": historical_awards,
    "WINNER_SECTOR_PATTERNS": historical_awards,
    "WINNER_IMPACT_BENCHMARKS": historical_awards,
    "APPLICATION_VOLUME_TRENDS": historical_awards,
    "WINNER_PATTERN_THRESHOLDS": benchmark_thresholds,
    "BENCHMARK_SCORE_POINTS": benchmark_thresholds,
    "BENCHMARK_METRIC_WEIGHTS": benchmark_thresholds,
}

#: Well below today's 69 so ordinary growth does not trip it, well above zero
#: so a broken sweep does.
MIN_CONSTANTS = 40


def _corpus_keys() -> list:
    """``["DICT.key", ...]`` for every top-level key in the corpus."""
    names = []
    for dict_name, module in CORPUS.items():
        value = getattr(module, dict_name)
        for key in value:
            names.append(f"{dict_name}.{key}")
    return names


def _load_registry() -> dict:
    """``{"DICT.key": (kind, source)}`` from the registry file."""
    entries = {}
    with open(REGISTRY_PATH, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            if not raw.strip() or raw.startswith("#"):
                continue
            parts = raw.rstrip("\n").split(" | ", 2)
            assert len(parts) == 3, (
                f"{REGISTRY_PATH}:{lineno} is not `KIND | source | CONSTANT.key`: "
                f"{raw!r}"
            )
            kind, source, name = (p.strip() for p in parts)
            assert kind in KINDS, (
                f"{REGISTRY_PATH}:{lineno} has kind {kind!r}; expected one of "
                f"{sorted(KINDS)}"
            )
            assert source, f"{REGISTRY_PATH}:{lineno} has an empty source"
            assert name not in entries, (
                f"{REGISTRY_PATH}:{lineno} rules {name} twice. A duplicate row "
                "is the hazard DEEP_DISTRESS_MIN_PCT already demonstrated: the "
                "second silently wins and the first is never read again."
            )
            entries[name] = (kind, source)
    return entries


@pytest.fixture(scope="module")
def registry():
    return _load_registry()


@pytest.fixture(scope="module")
def corpus():
    return _corpus_keys()


# ---------------------------------------------------------------------------
# Vacuity guards
# ---------------------------------------------------------------------------

def test_the_corpus_is_still_present():
    """Every dict this gate claims to sweep must still exist and be non-empty."""
    missing = [
        f"{module.__name__}.{name}"
        for name, module in CORPUS.items()
        if not isinstance(getattr(module, name, None), dict)
        or not getattr(module, name)
    ]
    assert not missing, (
        f"{missing} is named in CORPUS but is absent or empty. If a dict was "
        "deleted, delete its rows and its CORPUS entry in the same commit -- "
        "leaving the name here makes this gate look wider than it is."
    )


def test_the_sweep_is_not_vacuous(corpus):
    assert len(corpus) >= MIN_CONSTANTS, (
        f"the corpus sweep found only {len(corpus)} constants; the "
        "winner-pattern dicts carry far more. A number this small means the "
        "sweep is about to pass over nothing."
    )


def test_the_registry_is_not_empty(registry):
    assert registry, (
        f"{REGISTRY_PATH} parsed to zero rows. Every assertion below would "
        "pass vacuously."
    )


# ---------------------------------------------------------------------------
# THE GATE
# ---------------------------------------------------------------------------

def test_every_scoring_constant_carries_an_attribution(corpus, registry):
    """A constant that feeds a score must say where it came from.

    THIS IS THE ASSERTION THE ROUND EXISTS FOR. A benchmark constant added
    tomorrow fails this test until somebody writes down its provenance -- which
    is the one thing that never happened across nine findings of the same
    class.
    """
    unattributed = sorted(name for name in corpus if name not in registry)
    assert not unattributed, (
        f"{len(unattributed)} scoring constant(s) have no row in "
        f"{os.path.basename(REGISTRY_PATH)}:\n\n"
        + "\n".join(f"  {n}" for n in unattributed)
        + "\n\nAdd a row: `CITED | <retrievable document> | <NAME>` if the "
        "value comes from somewhere, or `HOUSE | <why no source exists> | "
        "<NAME>` if it does not. A HOUSE row is a declaration that the number "
        "is unsourced and a standing candidate for deletion -- not a way to "
        "keep it quietly. Do not delete this test to make it pass."
    )


def test_no_attribution_rules_a_constant_that_is_gone(corpus, registry):
    """A ruling that guards nothing reads as coverage.

    The 1.4.0 rural deletion left ``WINNER_PATTERN_THRESHOLDS["min_rural_pct"]``
    correctly removed -- but nothing in the suite would have noticed if its
    ruling had been left behind, and a registry accumulating dead rows looks
    more thorough every time it gets less accurate.
    """
    live = set(corpus)
    dead = sorted(name for name in registry if name not in live)
    assert not dead, (
        f"{len(dead)} row(s) in {os.path.basename(REGISTRY_PATH)} rule a "
        "constant that no longer exists:\n\n"
        + "\n".join(f"  {n}" for n in dead)
        + "\n\nDelete the rows in the same commit as the constants."
    )


def test_house_rows_outnumber_nothing_silently(corpus, registry):
    """State the unsourced count, and make a change to it deliberate.

    NOT A QUALITY BAR -- a count on its own says nothing about whether the
    right constants are unsourced. What it forbids is the count MOVING without
    anyone noticing: adding an unsourced constant, or quietly re-labelling one
    CITED, changes this number and fails until somebody re-derives it. That is
    the property EXPECTED_DEFECTS has in
    tests/test_fund_attribution_source.py, applied to values.

    IT IS AN EQUALITY, and it is high on purpose. 60 of 69 winner-pattern
    constants are unsourced. That number is the round's actual finding and it
    should be uncomfortable to look at; a bound like "<= 70" would let it drift
    upward and still read green.

    THE COUNT WAS DERIVED BY RUNNING THIS TEST, not typed in advance -- the
    first draft guessed 59 and this assertion caught it, which is the same
    class of hand-typed count that put FLOOR through five stale values in
    release.yml.

    61 -> 60 IN 1.5.0 F5, and the direction is the whole point of the gate.
    NMTC_AWARD_ROUNDS.CY2024 was HOUSE because its own comment said "Award data
    pending --- using estimated projections based on prior rounds". The round
    had in fact been awarded on 23 Dec 2025, thirteen months earlier; the row
    is now CY2024-2025 and CITED to the CY 2024-2025 NMTC Program Award Book.
    One constant left the unsourced set BY BEING SOURCED, which is the only
    direction this number is allowed to fall for a good reason.
    """
    house = sorted(n for n in corpus if registry.get(n, ("", ""))[0] == "HOUSE")
    assert len(house) == 60, (
        f"{len(house)} of {len(corpus)} winner-pattern constants are HOUSE "
        "(unsourced); this gate was last derived at 60 of 69.\n\n"
        "If the count went DOWN because something was sourced or deleted, "
        "lower this number and say so in CHANGELOG.md. If it went UP, a new "
        "unsourced constant entered a score -- which is the class this whole "
        "module exists to stop -- and the right response is to remove it, not "
        "to raise the number."
    )
