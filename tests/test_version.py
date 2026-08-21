"""Ensure __version__ and package metadata stay in sync.

THE TEST THAT WAS HERE COMPARED A VALUE TO ITSELF (1.5.0 S6).

    def test_version_sync():
        assert nmtcapp.__version__ == importlib.metadata.version("nmtc-application-builder")

and ``nmtcapp/__init__.py:42`` is::

    __version__ = _pkg_version("nmtc-application-builder")

The right-hand side is the left-hand side's DEFINITION. There is no state of the
world in which they disagree, so the assertion could not fail -- in the one file
whose entire subject is version integrity.

It is the shape rule 1 of ``tests/test_pinned_constants.py`` names: "A test that
reads a constant and compares it to itself cannot fail -- that is the shape of
the version guard that read installed metadata." That sentence was written about
THIS test, and the test outlived it by two releases.

The real assertion lives in
``tests/test_small_claims.py::test_version_is_checked_against_a_second_source``,
which compares ``__version__`` to ``pyproject.toml`` -- an independently edited
source, and the one a release bump actually touches.

WHAT IS KEPT HERE, because it is not a tautology: that the metadata is
RESOLVABLE at all. ``__init__`` swallows every exception and falls back to
"0.0.0.dev", so an install with broken metadata reports a plausible version
instead of failing. That fallback is invisible to a comparison against
pyproject.toml only if the fallback never fires; this makes it fire loudly.
"""
import importlib.metadata

import pytest

import nmtcapp


def test_version_metadata_resolves():
    """The distribution must be installed and its version readable.

    NOT A TAUTOLOGY. This asserts that ``importlib.metadata`` can find the
    distribution at all -- which it cannot in a source tree that was never
    installed, and which is exactly when ``__init__``'s bare ``except
    Exception`` quietly substitutes "0.0.0.dev".
    """
    try:
        resolved = importlib.metadata.version("nmtc-application-builder")
    except importlib.metadata.PackageNotFoundError:  # pragma: no cover
        pytest.fail(
            "nmtc-application-builder is not installed, so "
            "importlib.metadata cannot resolve its version and "
            "nmtcapp.__version__ has silently fallen back to '0.0.0.dev'. "
            "Install it: pip install -e '.[dev]'"
        )
    assert resolved, "metadata resolved to an empty version string"


def test_the_fallback_version_is_not_what_ships():
    """``0.0.0.dev`` means __init__'s except branch fired.

    The fallback exists so an uninstalled source tree can still be imported.
    It must never be what a test run sees, because every version assertion in
    the suite would then be comparing against a placeholder -- passing or
    failing for reasons unrelated to the release.
    """
    assert nmtcapp.__version__ != "0.0.0.dev", (
        "nmtcapp.__version__ is the '0.0.0.dev' fallback, so "
        "nmtcapp/__init__.py's `except Exception` branch fired and the real "
        "version was never read. Reinstall: pip install -e '.[dev]'"
    )
