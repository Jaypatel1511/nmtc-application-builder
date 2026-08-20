"""THE DEPLOYMENT GATE: the Streamlit app's pin, and the symbols it has to carry.

WHAT THIS CLOSES

`streamlit_app/requirements.txt` pins the app to a published copy of this
package. Nothing tied that pin to `pyproject.toml`, so it sat at 1.2.0 --- last
written by f71ebbc, the 1.2.0 release commit --- through 1.2.1, 1.3.0 and 1.3.1
without a single red tick, while the app's *source* deploys from the branch.

The failure that surfaced it: `1_Pipeline_Analyzer.py:26` imports
`join_truncated`, which is new in 1.3.1, and the deployed page raised
ImportError on a public URL.

WHY THE GATE THAT EXISTED DID NOT CATCH IT

`tests/test_streamlit_page_imports.py` was written for exactly this and its
docstring claims it catches "a PyPI-installed nmtc-application-builder
shadowing the local repo version". It cannot, and it did not, because its list
is TYPED rather than DERIVED. `test_page1_imports` mirrors three of page 1's
nine imported names. `join_truncated` is not among them, and neither are
`LIC_ROW_LABEL`, `NATIVE_AREA_ROW_LABEL`, `Q25_QEI_BASIS_CLAUSE` or
`q25_basis_note`. A human has to remember to update it, and across three
releases nobody did --- which is rule 4 of tests/test_pinned_constants.py (THE
LIST IS DERIVED, NOT INHERITED) violated in the one place it most mattered.

So: derive both sides, type neither.

THE TWO GATES

  1. test_the_streamlit_pin_matches_the_packaged_version parses the pinned
     version out of the requirements file and the version out of pyproject.toml
     and asserts equality. Neither number is typed here.

  2. test_every_streamlit_nmtcapp_import_resolves walks the AST of every file
     under streamlit_app/ for `from nmtcapp... import ...` and asserts each
     imported name exists in the installed package.

     WHEN IT WOULD FIRST HAVE GONE RED: 1.3.0, not 1.2.1. Derived, by
     resolving each tag's streamlit_app against the 1.2.0 that the pin held
     from f71ebbc onward::

         v1.2.0   GREEN
         v1.2.1   GREEN
         v1.3.0   RED   (11 unresolved: _question_25 absent,
                         HOUSE_TOP_TIER_* renamed from TOP_TIER_*)
         v1.3.1   RED   (14 unresolved: the above plus join_truncated,
                         LIC_ROW_LABEL, NATIVE_AREA_ROW_LABEL)

     So the gate buys ONE release of warning, not two: 1.2.1 changed no symbol
     the app imports. Both the 1.3.1 planning note and an earlier draft of this
     docstring said 1.2.1; the tag matrix above says otherwise and the tag
     matrix is derived.

HOW THE TWO COMPOSE. Gate 2 resolves against whatever `nmtcapp` is importable,
which under CI is this tree installed by `pip install ".[dev]"`. That is a
statement about the PINNED version only because gate 1 forces the pin to equal
this tree's version. Gate 1 red makes gate 2's scope a lie, so they are one
unit and neither is optional.

FAIL CLOSED, in the three ways this repository has been bitten before:

  - A MISSING PIN IS RED, NOT SKIPPED. Deleting the line must not become the
    way this goes green. `_pinned_version` raises when the requirement is
    absent instead of returning None and letting an `if` swallow it.
  - AN EMPTY WALK IS RED. If the AST sweep finds no nmtcapp imports at all,
    the walk broke; `all()` over an empty list is True and the gate would pass
    vacuously. Round nine was a grep against the wrong path set returning
    silence, and silence reading as absence.
  - NO tomllib. It is 3.11+; requires-python is >=3.9 and CI runs 3.9. An
    `import tomllib` here would fail on the two oldest interpreters, and a
    try/except-skip would make the gate silently absent exactly there. Regex,
    per the precedent in tests/test_121_financial_tables.py.

WHAT THESE GATES CANNOT SEE

  - RUNTIME ATTRIBUTE ACCESS. `analysis.impact_summary["x"]`, `getattr(...)`,
    anything reached after import. Only import-time names are static.
  - CHANGED BEHAVIOUR BEHIND AN UNCHANGED SIGNATURE. A function that still
    exists and still takes the same arguments but computes a different number
    resolves clean here. That is the silent half and this gate does not reach
    it.
  - ANY PAGE NOT UNDER streamlit_app/. The walk is scoped to that directory.
  - WHETHER THE PUBLISHED ARTIFACT MATCHES THE TREE. Gate 2 resolves against
    this tree, not against the wheel actually on PyPI for that version. If a
    release ever shipped a wheel whose contents differ from its tag, both gates
    stay green and the deployed app still breaks. tests/test_wheel_completeness
    is the neighbouring question; this one does not answer it.
  - WHAT THE DEPLOYMENT ACTUALLY INSTALLED. A pin is a request. Nothing here
    reads the running environment on Streamlit Cloud.
"""
import ast
import importlib
import os
import re

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REQUIREMENTS = os.path.join(_ROOT, "streamlit_app", "requirements.txt")
_STREAMLIT_APP = os.path.join(_ROOT, "streamlit_app")
_DISTRIBUTION = "nmtc-application-builder"


def _pinned_version():
    """The version `streamlit_app/requirements.txt` pins this package to.

    RAISES when the requirement is absent. Returning None would let a caller
    write `if pinned and pinned != packaged`, under which deleting the line is
    how the gate goes green --- the precise shape this gate exists to forbid.
    """
    with open(_REQUIREMENTS, encoding="utf-8") as fh:
        text = fh.read()

    # Match the distribution by name, tolerating the underscore spelling and
    # surrounding whitespace, so a cosmetic rewrite of the file does not read
    # as a missing pin.
    pattern = re.compile(
        r"^\s*nmtc[-_]application[-_]builder\s*==\s*([^\s;#]+)\s*$",
        re.MULTILINE | re.IGNORECASE,
    )
    found = pattern.findall(text)
    if not found:
        raise AssertionError(
            "streamlit_app/requirements.txt does not pin "
            f"{_DISTRIBUTION}==<version>. The Streamlit app installs a "
            "published copy of this package alongside the repository it "
            "deploys from; without an == pin the deployed app runs whatever "
            "version PyPI last published, which is how the app served 1.2.0 "
            "analysis under 1.3.1 source. Removing the line is not a way to "
            "satisfy this gate."
        )
    if len(found) > 1:
        raise AssertionError(
            f"{_DISTRIBUTION} is pinned {len(found)} times in "
            f"streamlit_app/requirements.txt: {found}. pip takes the last, "
            "so a duplicate pin is a silent override."
        )
    return found[0]


def _packaged_version():
    """The version declared in pyproject.toml's [project] table.

    Scoped to [project] on purpose: a bare `^version = ` sweep would also match
    a `version` key in any other table and pick whichever came first.
    """
    with open(os.path.join(_ROOT, "pyproject.toml"), encoding="utf-8") as fh:
        text = fh.read()

    block = re.search(r"^\[project\]\s*$(.*?)(?=^\[)", text,
                      re.MULTILINE | re.DOTALL)
    assert block, "pyproject.toml has no [project] table"
    version = re.search(r'^\s*version\s*=\s*"([^"]+)"\s*$', block.group(1),
                        re.MULTILINE)
    assert version, "pyproject.toml's [project] table declares no version"
    return version.group(1)


def test_the_streamlit_pin_matches_the_packaged_version():
    """Both sides derived. Neither number appears as a literal in this file."""
    pinned = _pinned_version()
    packaged = _packaged_version()
    assert pinned == packaged, (
        f"streamlit_app/requirements.txt pins {_DISTRIBUTION}=={pinned} but "
        f"pyproject.toml declares version {packaged}.\n\n"
        "The Streamlit app deploys its SOURCE from the branch and installs "
        "this package from PyPI beside it. When the two disagree, the "
        "installed copy shadows the repository and the pages compute with the "
        "older code --- loudly if a page imports a name the pinned version "
        "lacks, and SILENTLY if it does not."
    )


def _streamlit_nmtcapp_imports():
    """Every (file, lineno, module, name) imported from nmtcapp under streamlit_app/.

    Derived by AST walk, not by grep: a grep for `from nmtcapp` misses nothing
    here, but it also cannot tell an import inside a function body from one at
    module scope, and it cannot enumerate the names inside a parenthesised
    multi-line import without re-implementing the parser. ast.walk reaches
    both, including the deferred imports inside
    2_Win_Alignment_Scorer.py's button handler.
    """
    found = []
    for dirpath, dirnames, filenames in os.walk(_STREAMLIT_APP):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            path = os.path.join(dirpath, filename)
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom):
                    continue
                if node.level:            # relative import, not ours
                    continue
                module = node.module or ""
                if module != "nmtcapp" and not module.startswith("nmtcapp."):
                    continue
                for alias in node.names:
                    found.append((
                        os.path.relpath(path, _ROOT), node.lineno,
                        module, alias.name,
                    ))
    return found


def test_the_import_walk_finds_something():
    """FAIL CLOSED. An empty walk would make the gate below pass vacuously.

    Separate from the resolution test on purpose: if the sweep silently
    returned nothing --- a moved directory, a renamed package, a parse that
    stopped finding ImportFrom --- `for` over an empty list executes no
    assertion and reports green. This is round nine's defect (a search against
    the wrong path set returning silence, and silence reading as absence)
    stated as its own gate so it cannot hide inside another one.
    """
    imports = _streamlit_nmtcapp_imports()
    assert imports, (
        f"no `from nmtcapp... import ...` statements found under "
        f"{_STREAMLIT_APP}. The Streamlit pages import nmtcapp on their first "
        "lines, so finding none means the walk broke, not that the imports "
        "went away."
    )
    # The four pages plus utils.py all import nmtcapp. Anything less means the
    # sweep reached only part of the tree.
    files = {rel for rel, _, _, _ in imports}
    assert len(files) >= 5, (
        f"the walk reached only {sorted(files)}; expected at least the four "
        "pages and utils.py"
    )


def test_every_streamlit_nmtcapp_import_resolves():
    """Every name the Streamlit app imports from nmtcapp must exist.

    Import-time symbol existence is statically enumerable and dynamically
    checkable, and this is the check that would have gone red at 1.3.0 ---
    when _question_25 arrived and TOP_TIER_* became HOUSE_TOP_TIER_* --- rather
    than at 1.3.1, when a page finally imported a name new enough to crash on
    arrival. One release of warning; see the module docstring for the derivation.
    """
    unresolved = []
    for rel, lineno, module, name in _streamlit_nmtcapp_imports():
        try:
            imported = importlib.import_module(module)
        except Exception as exc:  # noqa: BLE001 - the reason is the report
            unresolved.append(f"{rel}:{lineno}  {module} ({type(exc).__name__}: {exc})")
            continue
        if name == "*":
            continue
        if hasattr(imported, name):
            continue
        # `from pkg import submodule` binds a module, not an attribute, and
        # hasattr is False until it has been imported at least once.
        try:
            importlib.import_module(f"{module}.{name}")
        except Exception:  # noqa: BLE001
            unresolved.append(f"{rel}:{lineno}  {module}.{name}")

    assert not unresolved, (
        "Streamlit pages import names that do not exist in the installed "
        "nmtcapp:\n  " + "\n  ".join(unresolved) + "\n\n"
        "On Streamlit Cloud these are the pages that show an ImportError "
        "instead of a report."
    )


def test_the_pin_is_a_version_the_gate_can_compare():
    """A pin must be an exact ==, not a range.

    `>=1.3.1` would satisfy a naive equality check only by accident and would
    let the deployed app drift forward silently on the next release --- the
    same class of skew, in the other direction.
    """
    pinned = _pinned_version()
    assert re.fullmatch(r"\d+\.\d+\.\d+", pinned), (
        f"the Streamlit pin resolves to {pinned!r}, which is not an exact "
        "three-part version. The deployed app must install one known version."
    )


@pytest.mark.parametrize("page", [
    "1_Pipeline_Analyzer.py",
    "2_Win_Alignment_Scorer.py",
    "3_Pipeline_Optimizer.py",
    "4_About_and_Methodology.py",
])
def test_each_page_has_its_imports_covered_by_the_walk(page):
    """Each page is reached by the sweep, named individually.

    The aggregate count in test_the_import_walk_finds_something proves the walk
    found five files; it does not prove WHICH five. A page renamed or moved out
    of pages/ would keep the count and lose the coverage.
    """
    reached = {rel for rel, _, _, _ in _streamlit_nmtcapp_imports()}
    expected = os.path.join("streamlit_app", "pages", page)
    assert expected in reached, (
        f"{expected} contributes no nmtcapp imports to the walk. Either the "
        "page moved, or the sweep no longer reaches pages/."
    )
