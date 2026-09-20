"""A published test count must be the tree's, not a person's memory.

THE DEFECT THIS GATE EXISTS FOR (1.3.1 F3)
==========================================

Two rendered surfaces stated a test count and neither was right:

    streamlit_app/app.py:86    "✅ 890+ tests"      on the landing page footer,
                               beside "MIT License" and a data-provenance line
    README.md:289              "# 544 tests, should all pass"  in the block a
                               contributor copies to run the suite

AND A THIRD, WHICH THIS GATE MISSED UNTIL 1.3.1's FIX ROUND:

    CONTRIBUTING.md:27         "# all 544 tests"    stale by 600 against the
                               1,144 the tree collected at 30e8146, in the
                               file that tells a contributor what to run

The miss is worth stating plainly, because it is this gate's own class of
defect one layer in. The docstring below said every surface that states a
test count states this one, and _CLAIM_SITES held two of the three. The third
was not hidden: it is the same command on the same kind of line, differing
only by the word `all`, which the README pattern had no alternative for. A
gate that names its coverage in prose and enumerates it in a tuple can have
the prose be the wrong one, and nothing here compared them.

AND A FOURTH, ADDED IN 1.7.1 R10 — AND IT WAS NOT WRONG HERE
============================================================

    CHANGELOG.md               "Published test counts re-derived: X → Y",
                               in the current release entry

This branch's number is correct, so this is a HOLE being closed, not a
falsehood being fixed. The hole is real: a PARALLEL IMPLEMENTATION of this
same 1.7.1 published "was 1,909" against a v1.7.0 that collects 1,896 — a
number that contradicted the three files its own branch had just corrected —
and nothing caught it, because the CHANGELOG was not a claim site. The
paragraph below has named the CHANGELOG since 1.3.1 as evidence that
hand-typed counts go stale; it was never a site this gate read.

It is scoped to the CURRENT entry. Released entries below state counts that
are true as history, and a gate that reddens on a true sentence is a gate
somebody deletes instead of fixing. See ``_current_changelog_entry`` and
``test_the_changelog_claim_is_scoped_to_the_current_entry``, which proves the
scope is load-bearing rather than asserting that it is.

The tree collected 1,097 at ``0643296``. This README has been wrong about its
own test count at 658, at 544 and at 890+ — three times, in the direction that
makes the package look smaller than it is on one surface and rounder than it is
on the other. A contributor who runs the README's command and sees a different
number has no way to tell a stale comment from a broken checkout.

WHY A CORRECTED NUMBER IS NOT THE FIX
=====================================

The number was corrected in 1.2.0 and went stale again by 1.3.0. A count with
nothing holding it is a count that will be wrong by 1.4.0, and this package's
own CHANGELOG documents six hand-typed counts going stale for exactly this
reason. So the surfaces state the number and this gate DERIVES it, the way a
reader would: by collecting the suite.

HOW IT DERIVES IT, AND WHAT THAT COSTS
======================================

``pytest --collect-only -q`` in a subprocess, against the same ``tests/``
directory the README tells a contributor to run. Collection does not execute
anything, so this cannot recurse. It takes about a second.

THE COUNT IS ENVIRONMENT-DEPENDENT AND THAT IS WHY THE FLOOR EXISTS.
Several test modules ``pytest.importorskip`` at import time, so a machine
without reportlab or python-docx collects fewer. Every one of those libraries
is in the ``dev`` extra, which is what CI installs and what CONTRIBUTING tells
a contributor to install, so the count is exact there. On a partial install the
gate says so and skips rather than reporting a false red — and the floor below
is what stops that courtesy from becoming the way it passes.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Test modules that skip themselves when an optional library is absent. If all
#: of these import, the collection count is the full one and the claims must
#: match it exactly.
_OPTIONAL_IMPORTS = ("reportlab", "pypdf", "docx", "openpyxl", "matplotlib",
                     "streamlit", "plotly", "yaml", "pandas")

#: Below this, collection did not really run and this gate would be comparing
#: a claim against nothing. Not a pin on the count — a floor under the
#: MEASUREMENT, the same shape as `assert measured > 0` in the frame gates.
_MIN_PLAUSIBLE_COLLECTION = 800

#: THE FOURTH SURFACE'S PATTERN (1.7.1 R10). The CHANGELOG states its
#: re-derived published count as ``old → new``; the NEW one is the claim about
#: this tree and is what group 1 captures. The bold alternatives are there
#: because the sentence has been written both ways -- ``Published test counts
#: re-derived: 1,896 → 1,961`` in the 1.7.1 entry and ``Published test count
#: **1,783 → 1,790**`` in 1.6.2's -- and a pattern that only knows this
#: round's spelling is the same one-alternative blindness that hid
#: CONTRIBUTING.md for a whole release.
_CHANGELOG_COUNT_RE = (
    r'Published test counts? (?:re-derived: )?\**[\d,]+\**\s*→\s*\**([\d,]+)\**'
)

#: The surfaces that publish a test count, the pattern that captures it, and
#: the region of the file that pattern is applied to. The pattern must capture
#: the NUMBER in group 1, so this compares what it captured against what it
#: collected — not merely that some digits are there. A ``None`` scope means
#: the whole file; a callable is handed the file's text and returns the slice
#: the claim lives in.
_CLAIM_SITES = (
    ("streamlit_app/app.py", r'"✅\s*([\d,]+)\+?\s*tests', None),
    ("README.md", r'pytest tests/[^\n#]*#\s*(?:all\s+)?([\d,]+)\+?\s*tests', None),
    # THE THIRD SURFACE, ADDED IN 1.3.1's FIX ROUND. This gate's docstring said
    # every surface stating a test count states this one, and it read two of
    # three. CONTRIBUTING.md carried `# all 544 tests` against a tree that
    # collected 1,144 -- stale by 600, in the file that tells a contributor
    # what to run. It was missed because the README pattern had no `all `
    # alternative, so the same line shape did not match here; the alternative
    # is now in both patterns rather than in a third one that can drift.
    ("CONTRIBUTING.md",
     r'pytest tests/[^\n#]*#\s*(?:all\s+)?([\d,]+)\+?\s*tests', None),
    # THE FOURTH SURFACE, ADDED IN 1.7.1 R10, AND IT CLOSES A HOLE RATHER THAN
    # A FALSEHOOD. This branch's CHANGELOG count is correct. A PARALLEL
    # IMPLEMENTATION OF THIS SAME RELEASE SHIPPED A FALSE ONE -- it published
    # "was 1,909" against a v1.7.0 that collects 1,896, contradicting the three
    # files corrected in its own branch -- and nothing caught it, because the
    # CHANGELOG was not a claim site. It is the surface a CDE and a downstream
    # maintainer read WITHOUT running anything, which is the argument the
    # existing changelog-figure gates in tests/test_pinned_constants.py already
    # make for the sweep counts.
    #
    # SCOPED TO THE CURRENT ENTRY, AND THE SCOPE IS THE WHOLE DESIGN. Headings
    # below state counts that are TRUE AS HISTORY -- 1,881 under 1.6.5, 1,790
    # under 1.6.2 -- so an unscoped pattern would go red on a true sentence,
    # which is how a gate gets deleted instead of fixed. Measured: with the
    # scope removed this site reads 1,790 out of the 1.6.2 entry and fails.
    ("CHANGELOG.md", _CHANGELOG_COUNT_RE, lambda text: _current_changelog_entry(text)),
)

#: The heading that opens a released entry. `## [1.7.1] — 2026-09-19`.
_ENTRY_HEADING_RE = re.compile(r"^## \[", re.MULTILINE)


def _current_changelog_entry(text: str) -> str:
    """CHANGELOG.md from its newest release heading to the one below it.

    Keep a Changelog puts the newest entry first, so the current entry is
    everything between heading 1 and heading 2. Raises rather than returning
    the whole file if it cannot find two headings: a scoper that silently
    degrades to "the whole document" is how a bounded gate becomes an
    unbounded one without anybody editing it.
    """
    heads = [m.start() for m in _ENTRY_HEADING_RE.finditer(text)]
    assert len(heads) >= 2, (
        f"CHANGELOG.md has {len(heads)} '## [' release heading(s); this scoper "
        "needs two to bound the current entry. If the heading shape changed, "
        "fix the regex — do not fall back to scanning the whole file, which "
        "would make this claim site red on entries that are true as history."
    )
    return text[heads[0]:heads[1]]


def _collect_count() -> int:
    """The number ``pytest tests/ --collect-only -q`` reports, in this env."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q",
         "-p", "no:cacheprovider"],
        cwd=_ROOT, capture_output=True, text=True,
    )
    match = re.search(r"(\d+)\s+tests?\s+collected", proc.stdout)
    assert match, (
        "could not read a collection count out of pytest's own output. The "
        "summary line changed shape; read it and fix the regex rather than "
        "deleting the check.\n\n" + proc.stdout[-2000:] + proc.stderr[-1000:]
    )
    return int(match.group(1))


@pytest.fixture(scope="module")
def collected() -> int:
    missing = []
    for name in _OPTIONAL_IMPORTS:
        try:
            __import__(name)
        except ImportError:
            missing.append(name)
    if missing:
        pytest.skip(
            f"{', '.join(missing)} not installed, so some test modules skip at "
            "import and the collection count here is not the full one. "
            'Install with `pip install -e ".[dev]"`, which is what CI does.'
        )
    count = _collect_count()
    assert count >= _MIN_PLAUSIBLE_COLLECTION, (
        f"collection reported {count} tests, below the {_MIN_PLAUSIBLE_COLLECTION} "
        "floor. Collection is broken, not the claim — and a gate that "
        "compares a published number against a broken measurement is worse "
        "than no gate."
    )
    return count


@pytest.mark.parametrize("relpath,pattern,scope", _CLAIM_SITES,
                         ids=[s[0] for s in _CLAIM_SITES])
def test_a_published_test_count_is_the_one_the_tree_collects(
    relpath, pattern, scope, collected
):
    """Every surface that states a test count states this one."""
    path = os.path.join(_ROOT, *relpath.split("/"))
    if not os.path.exists(path):
        # THE SDIST JOB DOES NOT PUT EVERY SURFACE BESIDE tests/. It copies
        # only tests/, streamlit_app/, README.md and pyproject.toml out of the
        # tarball, so CONTRIBUTING.md and CHANGELOG.md are shipped but not
        # present at runtime there. Found by running this round's change
        # through the job's actual invocation, where it was a
        # FileNotFoundError rather than a skip.
        #
        # A skip and not a pass, and it cannot become the way this goes green
        # on a checkout: _ALWAYS_PRESENT_CLAIM_SITES below is asserted to exist
        # unconditionally, so the two shipped surfaces are never skippable.
        pytest.skip(
            f"{relpath} is not beside tests/ (this is the sdist job's run "
            "directory or an installed tree, not a checkout). It ships in the "
            "tarball; the job simply does not copy it out."
        )
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if scope is not None:
        whole = text
        text = scope(whole)
        assert text and len(text) < len(whole), (
            f"{relpath}: the scoper returned {len(text)} of {len(whole)} "
            "characters. It is supposed to narrow the file to the region the "
            "claim lives in; returning everything, or nothing, is not a scope."
        )

    matches = re.findall(pattern, text)
    assert matches, (
        f"{relpath} no longer states a test count in the form this gate "
        "recognises. If the sentence was reworded, reword the pattern — do "
        "not delete the check. This claim has been wrong three times (658, "
        "544, 890+) and each correction outlived its next release."
    )
    for raw in matches:
        claimed = int(raw.replace(",", ""))
        assert claimed == collected, (
            f"{relpath} says {raw} tests; `pytest tests/ --collect-only -q` "
            f"reports {collected}. Re-derive it rather than rounding:\n\n"
            f"    pytest tests/ --collect-only -q | tail -1\n\n"
            "A '+' does not make a stale number true — 890+ was published "
            "against a tree that collected 1,097."
        )


#: Surfaces that are present wherever this suite can run at all. The skip above
#: is scoped to the surfaces the sdist job does not copy out; these two are not
#: allowed to take it, or "no claim site was readable" becomes a green run.
_ALWAYS_PRESENT_CLAIM_SITES = ("streamlit_app/app.py", "README.md")


def test_the_shipped_claim_sites_are_never_merely_skipped():
    """The two surfaces that travel with the suite must always be readable."""
    for relpath in _ALWAYS_PRESENT_CLAIM_SITES:
        path = os.path.join(_ROOT, *relpath.split("/"))
        assert os.path.exists(path), (
            f"{relpath} states a published test count and is not present, so "
            "the gate above skipped rather than checked it. This surface "
            "travels with the suite in every environment the suite runs in; if "
            "that has changed, the packaging changed and this gate is now "
            "blind, which is not something a skip should be allowed to say "
            "quietly."
        )
    assert set(_ALWAYS_PRESENT_CLAIM_SITES).issubset({s[0] for s in _CLAIM_SITES}), (
        "a surface listed as always-present is no longer a claim site at all"
    )


def test_the_derivation_would_notice_a_wrong_number(collected):
    """SENSITIVITY. The gate must reject the numbers that actually shipped."""
    for stale in (658, 544, 890):
        assert stale != collected, (
            f"the tree now collects exactly {stale}, which is one of the three "
            "numbers this package has published wrongly. Coincidence, but this "
            "proof is no longer a proof — pick a different witness."
        )
    pattern = _CLAIM_SITES[1][1]
    forged = "pytest tests/ -v          # 544 tests, should all pass"
    assert [int(m) for m in re.findall(pattern, forged)] == [544], (
        "the README pattern does not capture the number out of the exact line "
        "that shipped wrong — this gate would not have caught it"
    )

    # THE `all ` SHAPE, WHICH IS WHY THE THIRD SURFACE WAS MISSED (1.3.1 fix
    # round). CONTRIBUTING.md wrote `# all 544 tests` where README wrote
    # `# 544 tests`, and one absent alternative in the pattern was the whole
    # of the blindness. Both patterns carry it now, so assert both do.
    contributing_pattern = _CLAIM_SITES[2][1]
    forged_all = "PYTHONPATH=. pytest tests/ -v          # all 544 tests"
    for label, pat in (("README", pattern), ("CONTRIBUTING", contributing_pattern)):
        assert [int(m) for m in re.findall(pat, forged_all)] == [544], (
            f"the {label} pattern does not capture the number out of the exact "
            "`# all <n> tests` line that shipped wrong in CONTRIBUTING.md. That "
            "missing `all ` alternative is why this gate read two surfaces of "
            "three while its docstring claimed every one."
        )

    # THE FOURTH SURFACE'S SHAPE (1.7.1 R10), against the sentence a parallel
    # implementation of this same release actually shipped wrong, and against
    # the older bolded spelling the CHANGELOG has also used. Both must yield
    # the NEW count -- the right-hand side of the arrow -- and not the old one.
    changelog_pattern = _CLAIM_SITES[3][1]
    for forged_entry, expected in (
        ("* Published test counts re-derived: 1,909 → 1,939 in `README.md`,", 1939),
        ("* Published test count **1,783 → 1,790** in `README.md` and", 1790),
    ):
        got = [int(m.replace(",", ""))
               for m in re.findall(changelog_pattern, forged_entry)]
        assert got == [expected], (
            "the CHANGELOG pattern reads "
            f"{got} out of {forged_entry!r}; it must capture the re-derived "
            f"count {expected}. A parallel implementation of 1.7.1 published "
            "'was 1,909' against a v1.7.0 that collects 1,896 and nothing "
            "caught it, because this surface was not a claim site at all."
        )

    # AND IT MUST NOT CAPTURE THE COUNTS THAT ARE LEGITIMATELY DIFFERENT. The
    # current entry also records an `-m "not wheel"` collection and a passed
    # count, neither of which equals `pytest tests/ --collect-only -q`. A
    # pattern loose enough to pick those up would be red on true sentences.
    for innocent in (
        '1,938 collected under `-m "not wheel"`, 77 skipped,',
        "1,938 passed, 1 skipped (`network`)",
        "1,861 passed, 77 skipped, 1 deselected, zero failures",
    ):
        assert not re.findall(changelog_pattern, innocent), (
            f"the CHANGELOG pattern matches {innocent!r}, which states a "
            "different measurement on purpose. Tighten the pattern rather "
            "than loosening the comparison."
        )


def test_the_changelog_claim_is_scoped_to_the_current_entry(collected):
    """THE SCOPE IS LOAD-BEARING, AND THIS IS WHAT PROVES IT.

    Every released entry below the current one states the count that was true
    when it shipped. An unscoped pattern would compare those to today's tree
    and go red on sentences that are true as history — which is how a gate
    gets deleted instead of fixed, and why the scope exists rather than a
    looser comparison. Measured, with the scope removed: this site reads
    1,790 out of the 1.6.2 entry and fails against a tree collecting 1,960.

    Two-sided, so neither half can rot into decoration:

      * the scoped region is exactly the slice between the first two release
        headings, and contains no second heading; and
      * the SAME pattern applied to the WHOLE file yields at least one count
        that is not today's — i.e. an unscoped gate would be red right now.
    """
    path = os.path.join(_ROOT, "CHANGELOG.md")
    if not os.path.exists(path):
        pytest.skip("CHANGELOG.md is not beside tests/ (sdist run directory)")
    whole = open(path, encoding="utf-8").read()
    entry = _current_changelog_entry(whole)

    heads = [m.start() for m in _ENTRY_HEADING_RE.finditer(whole)]
    assert entry == whole[heads[0]:heads[1]], (
        "the scope is not the slice between the first two release headings"
    )
    assert len(entry) < len(whole), "the scope returned the whole file"
    assert _ENTRY_HEADING_RE.search(entry[2:]) is None, (
        "the scoped region contains a second release heading, so it is more "
        "than one entry and the history it excludes is back inside the gate"
    )

    pattern = _CLAIM_SITES[3][1]
    scoped = [int(m.replace(",", "")) for m in re.findall(pattern, entry)]
    assert scoped == [collected], (
        f"the current entry states {scoped} as its re-derived published count; "
        f"the tree collects {collected}"
    )

    unscoped = [int(m.replace(",", "")) for m in re.findall(pattern, whole)]
    assert len(unscoped) > len(scoped), (
        "the whole file yields no more count claims than the current entry, so "
        "the scope is not doing anything and this proof is decoration. If the "
        "older entries were reworded, say so here rather than deleting the "
        "scope: the next entry will bring the problem straight back."
    )
    assert any(value != collected for value in unscoped), (
        "every count claim in the whole CHANGELOG equals today's collection, "
        f"{collected}. That can only be a coincidence — the historical entries "
        "describe trees that collected fewer tests — so re-check the pattern "
        "before trusting it."
    )


# ---------------------------------------------------------------------------
# THE SAME CLASS, ON THE SAME PAGE: a count about the shipped sample
# ---------------------------------------------------------------------------

def test_the_landing_pages_sample_description_matches_the_shipped_sample():
    """"a 20-project pipeline spanning 12 states" — it spans 19.

    FOUND IN 1.3.1's USER-SURFACE READ, four lines above the test count. The
    landing page describes the demo pipeline a first-time visitor is about to
    load, and the description is hand-typed against a CSV that ships in this
    repository and can simply be read. A visitor who loads the sample and sees
    "States represented: 19" beside a landing page that said 12 has no way to
    tell which one the tool got wrong.

    Same class as the test count and the same remedy: state it, derive it.
    """
    from nmtcapp.core.pipeline import Pipeline

    # Resolved from the INSTALLED package, the way tests/conftest.templates_dir
    # does — so this runs in the sdist job too, whose test directory
    # deliberately carries no nmtcapp/ tree to shadow the installed one.
    import nmtcapp

    sample = os.path.join(os.path.dirname(nmtcapp.__file__), "templates",
                          "pipeline_sample_strong.csv")
    assert os.path.exists(sample), (
        "the sample pipeline the landing page describes is not packaged"
    )
    pipeline = Pipeline.from_csv(sample)
    projects = list(pipeline)
    states = {p.state for p in projects if p.state}

    with open(os.path.join(_ROOT, "streamlit_app", "app.py"), encoding="utf-8") as fh:
        page = fh.read()

    claim = re.search(r"a\s+(\d+)-project pipeline spanning\s+(\d+)\s+states", page,
                      re.S)
    assert claim, (
        "streamlit_app/app.py no longer describes the sample pipeline in the "
        "form this gate reads. Reword the pattern rather than dropping the "
        "check — the figure it holds was wrong by seven states."
    )
    assert int(claim.group(1)) == len(projects), (
        f"the landing page says a {claim.group(1)}-project pipeline; "
        f"{os.path.basename(sample)} has {len(projects)}"
    )
    assert int(claim.group(2)) == len(states), (
        f"the landing page says the sample spans {claim.group(2)} states; "
        f"{os.path.basename(sample)} spans {len(states)} "
        f"({', '.join(sorted(states))}). The Pipeline Analyzer prints the real "
        "number as 'States represented' the moment a visitor loads it."
    )
