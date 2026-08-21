"""The 1.4.1 S6 gates: four small defects, each closed as a class.

Each of these was a one-line fix. None of them is filed as one, because a
one-line fix is a site and this round exists to stop shipping sites.

  S6a  A PUBLISHED COUNT ABOUT THE SAMPLE PIPELINE. Two surfaces said the
       sample spans "12 states". It spans 19. Closed by deriving both claims
       from ``Pipeline.sample()`` -- the same shape as
       ``test_test_count_claims``, which exists because "890+ tests" was
       published against a tree collecting 1,097.

  S6b  A TEST THAT COMPARED A VALUE TO ITSELF. See
       ``test_version_is_checked_against_a_second_source``.

  S6c  A CEILING NOTHING WAS EVER MEASURED AGAINST. See
       ``test_max_sdist_skips_is_measured_against_something``.

  S6d  A LOGGING FORMAT STRING THAT CANNOT FORMAT. ``"$%,.0f"`` -- printf has
       no ',' flag -- raised ValueError inside logging on every Application
       construction at INFO. Nothing crashed, because logging catches its own
       formatting errors, prints a traceback to stderr and returns; so the
       message never appeared and no test noticed. Closed by checking EVERY
       %-style logging call in the package, not that one.
"""
from __future__ import annotations

import ast
import os
import re

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# S6a -- published counts about the sample pipeline
# ---------------------------------------------------------------------------

#: Each claim site: (path, regex with ONE group capturing the number).
#: The expected value is never typed here -- it is derived below.
_STATE_CLAIM_SITES = (
    ("streamlit_app/pages/1_Pipeline_Analyzer.py",
     r"20 realistic projects across (\d+) states"),
    ("streamlit_app/README.md",
     r"20 realistic projects across (\d+) states"),
)


def _sample_state_count() -> int:
    from nmtcapp.core.pipeline import Pipeline

    return len({p.state for p in Pipeline.sample(n=20)})


def test_the_sample_state_count_derivation_is_sane():
    """Guard the right-hand side before comparing anything to it."""
    count = _sample_state_count()
    assert 1 < count <= 20, (
        f"Pipeline.sample(n=20) reports {count} distinct states, which cannot "
        "be right for 20 projects. The derivation is broken, so every "
        "assertion below would be comparing against nonsense."
    )


@pytest.mark.parametrize("relpath,pattern", _STATE_CLAIM_SITES,
                         ids=[p for p, _ in _STATE_CLAIM_SITES])
def test_a_published_state_count_is_the_one_the_sample_holds(relpath, pattern):
    """A count published about the sample must equal the sample's own.

    BOTH SITES SAID 12 AND THE ANSWER IS 19 -- not a rounding, a different
    number. It was published for as long as the sentence existed, on the
    Streamlit page a CDE reads before uploading anything.
    """
    path = os.path.join(_REPO_ROOT, relpath)
    if not os.path.exists(path):
        pytest.skip(f"{relpath} absent (unpacked sdist, not a checkout)")

    with open(path, encoding="utf-8") as handle:
        text = handle.read()

    matches = re.findall(pattern, text)
    assert len(matches) == 1, (
        f"expected exactly one state-count claim in {relpath} matching "
        f"{pattern!r}; found {len(matches)}: {matches}. If the sentence was "
        "reworded, update the pattern -- a claim this gate cannot find is a "
        "claim it is not checking."
    )

    published = int(matches[0])
    actual = _sample_state_count()
    assert published == actual, (
        f"{relpath} says the sample pipeline spans {published} states; "
        f"Pipeline.sample(n=20) spans {actual}.\n\n"
        "Re-derive it rather than guessing:\n\n"
        "    len({p.state for p in Pipeline.sample(n=20)})\n\n"
        "Note the count is n-DEPENDENT -- sample(n=5) spans 5 states -- so a "
        "sentence stating a count must also state the n it belongs to."
    )


# ---------------------------------------------------------------------------
# S6b -- the version tautology
# ---------------------------------------------------------------------------

def test_version_is_checked_against_a_second_source():
    """``__version__`` must be compared to something that is not itself.

    THE TAUTOLOGY. ``tests/test_version.py`` asserted::

        nmtcapp.__version__ == importlib.metadata.version("nmtc-application-builder")

    and ``nmtcapp/__init__.py:42`` assigns::

        __version__ = _pkg_version("nmtc-application-builder")

    The right-hand side IS the left-hand side's definition. The test compares a
    value to itself and cannot fail on any disagreement -- which is rule 1 of
    tests/test_pinned_constants.py ("A test that reads a constant and compares
    it to itself cannot fail") demonstrated in the file whose whole job was
    version integrity.

    WHAT IT MISSED, AND IT IS THE ONLY FAILURE THAT MATTERS: pyproject.toml is
    where the version is actually EDITED for a release. Installed metadata is
    built FROM it, so on a stale editable install the two can disagree -- and
    the old test would agree with itself either way.

    NO tomllib: requires-python is >=3.9 and CI runs 3.9. Regex, per the
    precedent in tests/test_streamlit_deployment_pin.py.
    """
    import nmtcapp

    pyproject = os.path.join(_REPO_ROOT, "pyproject.toml")
    if not os.path.exists(pyproject):
        pytest.skip("pyproject.toml absent (installed tree, not a checkout)")

    with open(pyproject, encoding="utf-8") as handle:
        text = handle.read()

    matches = re.findall(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert len(matches) == 1, (
        f"expected exactly one top-level `version = \"...\"` in "
        f"pyproject.toml, found {len(matches)}: {matches}. Two assignments is "
        "the hazard DEEP_DISTRESS_MIN_PCT demonstrated -- the second silently "
        "wins."
    )
    declared = matches[0]

    assert nmtcapp.__version__ == declared, (
        f"nmtcapp.__version__ is {nmtcapp.__version__!r} but pyproject.toml "
        f"declares {declared!r}.\n\n"
        "These are two INDEPENDENT sources: pyproject.toml is edited by hand "
        "for a release, and __version__ is read from installed metadata built "
        "from it. A disagreement means the install is stale — reinstall with "
        "`pip install -e .` — or the release bump missed a site.\n\n"
        "Do not 'fix' this by comparing __version__ to importlib.metadata: "
        "that is where __version__ comes from, and the comparison cannot fail."
    )


# ---------------------------------------------------------------------------
# S6c -- a ceiling nothing is measured against
# ---------------------------------------------------------------------------

def test_max_sdist_skips_is_measured_against_something():
    """MAX_SDIST_SKIPS must bound an observable number, not just exist.

    WHAT IT WAS. ``tests/test_release_floor.MAX_SDIST_SKIPS`` is used in
    exactly one place: widening the lower bound of the FLOOR band. Nothing ever
    compared it to a skip count. Its own comment says "If the skip count ever
    approaches this, the right response is to ask why" -- and no code was
    watching, because that module runs from a CHECKOUT where the sdist-only
    tests do not skip, so it cannot observe the real number.

    A ceiling that nothing is measured against is not conservative. It is
    unfalsifiable, and it had already been wrong once: 1.3.0 justified 20 as
    "1.8x the measurement" against a measurement taken the forbidden way; run
    properly the ratio was 1.00x -- a ceiling exactly equal to the thing it
    bounded.

    WHAT THIS ASSERTS INSTEAD, and why it is honest about its own limits. The
    checkout cannot count sdist skips. It CAN count the tests that are
    STRUCTURALLY CAPABLE of skipping there -- the ones guarded by a checkout
    marker -- and that count is a genuine lower bound on the sdist's skips,
    derived from the tree rather than remembered. If it ever exceeds the
    ceiling, the ceiling is provably too low and the FLOOR band built on it is
    wrong.
    """
    from tests.test_release_floor import MAX_SDIST_SKIPS

    tests_dir = os.path.join(_REPO_ROOT, "tests")
    if not os.path.isdir(tests_dir):
        pytest.skip("tests/ not walkable here")

    #: What a deliberate sdist skip looks like: pytest.skip() reached because a
    #: tree the tarball does not ship is absent.
    markers = ("prune docs", "unpacked sdist", "not a checkout",
               "MANIFEST.in does not ship", "absent (this is an unpacked")

    capable = set()
    for dirpath, _dirs, names in os.walk(tests_dir):
        for name in sorted(names):
            if not name.startswith("test_") or not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            if "pytest.skip" not in text:
                continue
            if any(marker in text for marker in markers):
                capable.add(os.path.relpath(path, _REPO_ROOT))

    assert capable, (
        "found no test module carrying a checkout-marker skip. Either the "
        "markers changed or the walk broke; this assertion would then bound "
        "nothing, which is the exact property it was written to remove."
    )

    assert len(capable) <= MAX_SDIST_SKIPS, (
        f"{len(capable)} test MODULES can skip in an unpacked sdist, against "
        f"MAX_SDIST_SKIPS = {MAX_SDIST_SKIPS}. Since a module can contribute "
        "more than one skipping test, the true sdist skip count is at least "
        "this and probably higher, so the ceiling is provably too low and the "
        "FLOOR band derived from it is wrong.\n\n"
        "Re-derive both: build the sdist, run the release job's exact "
        "invocation from a directory holding only what the tarball shipped, "
        "and read the skip count off the summary. Do not raise the ceiling to "
        "buy room -- that is what made it an abstention before 1.3.0.\n\n"
        f"Modules that can skip: {sorted(capable)}"
    )


# ---------------------------------------------------------------------------
# S6d -- logging format strings that cannot format
# ---------------------------------------------------------------------------

def _logging_calls(tree: ast.AST):
    """Yield (lineno, format_string, arg_count) for %-style logging calls."""
    levels = {"debug", "info", "warning", "error", "critical", "exception", "log"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in levels:
            continue
        args = list(node.args)
        if node.func.attr == "log" and args:
            args = args[1:]          # drop the level argument
        if not args:
            continue
        fmt = args[0]
        # Only literal format strings are checkable; a joined/implicit-concat
        # literal arrives as a single Constant after parsing.
        if not (isinstance(fmt, ast.Constant) and isinstance(fmt.value, str)):
            continue
        if any(isinstance(kw.arg, str) and kw.arg == "exc_info"
               for kw in node.keywords):
            pass
        yield node.lineno, fmt.value, len(args) - 1


def test_every_logging_format_string_can_actually_format():
    """A %-format that raises is a message that never appears.

    ``logger.info("... allocation $%,.0f", value)`` raised
    ``ValueError: unsupported format character ','`` inside logging on every
    Application construction at INFO. It did not crash anything: logging
    catches formatting errors, prints a traceback to stderr, and returns. So
    the log line silently never appeared, and the only symptom was a traceback
    in the output of anyone running at INFO -- which no test asserted about.

    This checks the whole package rather than that one call, because the defect
    is "a format string nobody executed", and there is no reason it would
    occur once.
    """
    package = os.path.join(_REPO_ROOT, "nmtcapp")
    if not os.path.isdir(package):
        pytest.skip(
            "nmtcapp/ does not sit beside tests/ (this is an unpacked sdist, "
            "where the release job deliberately puts only tests/ and "
            "streamlit_app/ so the INSTALLED package is what gets imported). "
            "This gate reads package SOURCE, so it asks a question about the "
            "checkout."
        )
    broken, checked = [], 0

    for dirpath, _dirs, names in os.walk(package):
        for name in sorted(names):
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8") as handle:
                tree = ast.parse(handle.read())
            for lineno, fmt, argc in _logging_calls(tree):
                checked += 1
                try:
                    fmt % tuple(_Anything() for _ in range(argc))
                except (ValueError, TypeError) as exc:
                    broken.append(
                        f"  {os.path.relpath(path, _REPO_ROOT)}:{lineno}\n"
                        f"      {fmt!r}\n"
                        f"      {type(exc).__name__}: {exc}"
                    )

    assert checked >= 20, (
        f"only {checked} logging format strings were checked; this package "
        "carries far more. The AST walk is broken and this gate is passing "
        "over nothing."
    )
    assert not broken, (
        f"{len(broken)} logging call(s) have a format string that raises when "
        "applied to its arguments. logging swallows the error, so the message "
        "never appears and nothing fails -- it just prints a traceback to "
        "stderr for every user running at that level.\n\n"
        "printf has no ',' flag: use f\"{value:,.0f}\" as an argument and %s "
        "in the format.\n\n" + "\n".join(broken)
    )


class _Anything:
    """Satisfies any %-conversion, so only the FORMAT itself can fail.

    A real value would make this test about types -- ``%d`` against a str
    raises, and that is a different (and legitimate) call. What is being
    checked here is whether the format string is well-formed at all.
    """

    def __str__(self) -> str:
        return "x"

    def __repr__(self) -> str:
        return "x"

    def __float__(self) -> float:
        return 0.0

    def __int__(self) -> int:
        return 0

    def __index__(self) -> int:
        return 0


# ---------------------------------------------------------------------------
# S6e -- the Sample Output page rendered as its own source
# ---------------------------------------------------------------------------

def _sample_output_hook():
    import importlib.util

    path = os.path.join(_REPO_ROOT, "docs", "hooks", "generate_sample_output.py")
    if not os.path.exists(path):
        pytest.skip("docs/hooks absent (unpacked sdist, not a checkout)")
    spec = importlib.util.spec_from_file_location("_gso", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_sample_output_page_is_rendered_not_escaped():
    """The published page must be HTML, not its own Markdown source.

    ``_html()`` used to ``html.escape`` the body into a ``<pre>``. The page
    then showed a literal ``# Sample Output`` heading, an unlinked download
    list, and -- the half that matters -- the FICTIONAL-DATA WARNING as a raw
    ``!!! warning "..."`` marker.

    That warning is the page's most important content: it says the CDE in
    those documents does not exist and the files must not be filed. Displayed
    as markup noise above four downloadable federal application documents, it
    is the one sentence on the page a reader most needs to actually read.
    """
    hook = _sample_output_hook()
    page = hook._html(hook._PAGE_HEADER + "- [`app.docx`](app.docx)\n")

    assert "<pre" not in page, (
        "the Sample Output page is wrapped in <pre> again, so it publishes "
        "Markdown source rather than a rendered page."
    )
    assert "!!! warning" not in page, (
        "the admonition marker appears literally in the published HTML: the "
        "fictional-data warning is being shown as markup instead of as a "
        "warning."
    )
    assert 'class="admonition warning"' in page, (
        "the fictional-data warning did not render as an admonition. It is "
        "the sentence telling a reader not to file these documents."
    )
    assert '<a href="app.docx">' in page, (
        "the download list did not render as links, so the files a reader "
        "came for are not reachable."
    )
    assert "Riverbend Community Capital CDE" in page, (
        "the warning no longer names the fictional CDE by name"
    )


# ---------------------------------------------------------------------------
# Found BY this round, not listed in its brief: 3.9 f-string syntax
# ---------------------------------------------------------------------------

def _fstring_expressions_with_backslashes(source: str, path: str):
    r"""Yield (lineno, expression_source) for f-string expressions holding a ``\``.

    AST, NOT REGEX, and that is a measured decision rather than a stylistic
    one. The first draft of this gate used a regex and MISSED THE REAL LINE:
    the pattern could not cross the earlier ``{'Metric':<34}`` groups, whose
    quotes broke its character class, so it went green over the exact defect it
    was written for -- "a regex whose dots were wildcards", one of the recorded
    shapes of this project's false negatives.

    The parse cannot be fooled that way. Every ``FormattedValue`` inside a
    ``JoinedStr`` is located exactly, and its own source segment is read back.
    """
    tree = ast.parse(source, filename=path)
    for node in ast.walk(tree):
        if not isinstance(node, ast.JoinedStr):
            continue
        for part in node.values:
            if not isinstance(part, ast.FormattedValue):
                continue
            segment = ast.get_source_segment(source, part.value)
            if segment and "\\" in segment:
                yield getattr(part, "lineno", node.lineno), segment


def _python_sources(*trees):
    for tree in trees:
        root = os.path.join(_REPO_ROOT, tree)
        if not os.path.isdir(root):
            continue
        for dirpath, _dirs, names in os.walk(root):
            for name in sorted(names):
                if name.endswith(".py"):
                    yield os.path.join(dirpath, name)


def test_no_fstring_expression_contains_a_backslash():
    """``requires-python = ">=3.9"``, and this breaks the IMPORT on 3.9-3.11.

    FOUND BY THIS ROUND'S OWN WORK, and it is why the FLOOR derivation runs the
    sdist on 3.9 rather than trusting one interpreter. The 1.5.0 S3 rewrite of
    ``benchmarks.summary()`` introduced::

        f"  {'Metric':<34} {'Value':>8}   {'Band (this tool\\'s own)'}"

    which is fine on 3.12 -- the checkout venv -- and a **SyntaxError on
    3.9.25**, where ``nmtcapp.intelligence.benchmarks`` then fails to import at
    all. Every test touching benchmarks errored at collection.

    WHY NOTHING CAUGHT IT. ``tests/test_streamlit_page_py39.py`` guards PEP 604
    unions, and only under ``streamlit_app/``. Nothing checked ``nmtcapp/`` for
    3.9 syntax at all, and CI's 3.9 job runs the SDIST, so a checkout-only run
    on a modern interpreter is silent.

    WHY NOT ``ast.parse(feature_version=(3, 9))``. Measured, not assumed: it
    ACCEPTS this construct. CPython does not gate the f-string grammar change
    behind ``feature_version``, so the obvious mechanism does not work and a
    gate built on it would have passed over the exact defect it was written
    for. A regex is what actually detects it.
    """
    # THE CHECKOUT MARKER IS nmtcapp/, NOT "did the walk find anything".
    # An unpacked sdist ships streamlit_app/ and NOT nmtcapp/, so a
    # scanned == 0 guard does not fire there -- it finds seven modules, misses
    # the floor, and fails. Caught by running the sdist suite, which is the
    # same reason this gate exists at all.
    if not os.path.isdir(os.path.join(_REPO_ROOT, "nmtcapp")):
        pytest.skip(
            "nmtcapp/ does not sit beside tests/ (unpacked sdist). This gate "
            "reads package SOURCE and asks a question about the checkout."
        )

    offenders, scanned = [], 0
    for path in _python_sources("nmtcapp", "streamlit_app"):
        scanned += 1
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        for lineno, segment in _fstring_expressions_with_backslashes(source, path):
            offenders.append(
                f"  {os.path.relpath(path, _REPO_ROOT)}:{lineno}\n"
                f"      {{{segment[:100]}}}"
            )

    assert scanned >= 40, (
        f"scanned only {scanned} modules; the walk is broken and this gate is "
        "passing over nothing."
    )
    assert not offenders, (
        f"{len(offenders)} f-string(s) contain a backslash inside the "
        "expression part. That is a SyntaxError on Python 3.9, 3.10 and 3.11 "
        "-- the module does not import, so every test touching it errors at "
        "collection. requires-python is >=3.9.\n\n"
        "Bind the value to a local first:\n\n"
        "    label = \"Band (this tool's own)\"\n"
        "    f\"{label}\"\n\n" + "\n".join(offenders)
    )
