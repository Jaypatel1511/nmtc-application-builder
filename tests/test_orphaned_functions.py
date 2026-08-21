"""A module-private function with no caller is dead code that reads as live.

THE CLASS, AND WHY IT NEEDED ITS OWN GATE (1.5.0 F3)

1.5.0 deleted ``percentile_vs_winners`` and wrote in the CHANGELOG: "Gone, with
``_normal_cdf``, the ``Pctile`` column, the ``winner_std`` parameter and all six
literals." That was true of ``intelligence/benchmarks.py`` and FALSE OF THE
REPOSITORY. A byte-identical ``_normal_cdf`` survived at
``intelligence/win_probability.py:809`` -- no caller since ``8214788``, no test
covering it, and ``import math`` at the top of that module existing only to
serve it.

The round's S3 sweep enumerated CONSTANTS: every module-level dict in
``data/historical_awards.py`` plus Section B of ``data/benchmark_thresholds.py``,
one registry row per key, silence impossible. NOTHING ENUMERATED FUNCTIONS. So a
deletion could be complete in the module a reviewer had open and incomplete in
the tree, while the release notes asserted the tree.

That is the same shape as the constant problem and it deserves the same answer:
make silence impossible. This walks every module under ``nmtcapp/`` and fails on
a module-private ``def`` that no line in the package references.

WHY MODULE-PRIVATE ONLY. A public function is API: absence of an in-tree caller
proves nothing, because the caller may be a user's script. A leading-underscore
function is this package talking to itself, so this package is the whole
universe of callers, and zero of them means zero.

WHY A TEXT SCAN AND NOT A CALL-GRAPH. Names reach callers through
``getattr``, decorators, ``__all__`` and string dispatch, and a call-graph that
missed one of those would delete something live. A name that appears exactly
once in the entire package -- at its own ``def`` -- is unreachable by every one
of those routes at once. The scan is deliberately weaker than a call-graph and
that is what makes a hit conclusive.
"""
from __future__ import annotations

import ast
import os

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PACKAGE = os.path.join(_REPO_ROOT, "nmtcapp")

#: Names that are private by convention but called by the interpreter, not by
#: this package, so a zero-reference count says nothing about them.
_DUNDER_OR_HOOK = {
    "__init__", "__repr__", "__str__", "__eq__", "__hash__", "__post_init__",
    "__enter__", "__exit__", "__getattr__", "__iter__", "__len__",
}


def _require_package_tree() -> None:
    """This gate reads package SOURCE, which an unpacked sdist does not ship.

    MANIFEST.in puts tests/ and streamlit_app/ in the tarball and NOT
    nmtcapp/, and the release job runs the suite from a directory holding only
    what it copied out. So the walk finds nothing there -- and "found nothing"
    must be a skip, not a pass, or this gate would report every module clean in
    the one environment where it can see no modules at all.
    """
    if not os.path.isdir(_PACKAGE):
        pytest.skip(
            "nmtcapp/ does not sit beside tests/ (unpacked sdist). This gate "
            "reads package source and asks a question about the checkout."
        )


def _python_files() -> list:
    out = []
    for root, _dirs, files in os.walk(_PACKAGE):
        for name in sorted(files):
            if name.endswith(".py"):
                out.append(os.path.join(root, name))
    return sorted(out)


def _module_private_functions(path: str) -> list:
    """[(name, lineno)] for module-level ``def _name`` in this file.

    Methods are excluded: a private method is reached through an instance and
    may be overridden, so its name appearing once is not the same proof.
    """
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=path)
    found = []
    for node in tree.body:                      # module level only
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_") and node.name not in _DUNDER_OR_HOOK:
                found.append((node.name, node.lineno))
    return found


@pytest.fixture(scope="module")
def package_text() -> str:
    """Every .py file under nmtcapp/, concatenated. The universe of callers."""
    _require_package_tree()
    parts = []
    for path in _python_files():
        with open(path, encoding="utf-8") as fh:
            parts.append(fh.read())
    text = "\n".join(parts)
    assert len(text) > 100_000, (
        f"only {len(text)} chars of package source read — the walk is broken "
        "and this gate would pass vacuously"
    )
    return text


def test_the_scan_finds_functions_to_check(package_text):
    """Fail closed: no candidates means the AST walk broke, not that all is well."""
    _require_package_tree()
    total = sum(len(_module_private_functions(p)) for p in _python_files())
    assert total > 20, (
        f"only {total} module-private functions found across "
        f"{len(_python_files())} files — the AST walk is broken"
    )


def test_no_module_private_function_is_orphaned(package_text):
    """Every ``def _name`` in nmtcapp/ must be referenced somewhere in nmtcapp/."""
    orphans = []
    for path in _python_files():
        rel = os.path.relpath(path, _REPO_ROOT)
        for name, lineno in _module_private_functions(path):
            # One occurrence is the def itself. Anything reachable — a call, an
            # alias, a getattr string, an __all__ entry — is a second.
            if package_text.count(name) <= 1:
                orphans.append(f"  {rel}:{lineno}  {name}()")

    assert not orphans, (
        f"{len(orphans)} module-private function(s) are defined and never "
        "referenced anywhere in nmtcapp/:\n\n"
        + "\n".join(orphans)
        + "\n\nDelete them, along with any import that exists only to serve "
        "them. This gate exists because 1.5.0's CHANGELOG said `_normal_cdf` "
        "was gone while a byte-identical copy sat in win_probability.py with "
        "no caller since 8214788 — the sweep that round enumerated constants, "
        "and nothing enumerated functions."
    )
