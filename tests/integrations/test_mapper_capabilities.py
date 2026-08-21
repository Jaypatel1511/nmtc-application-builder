"""The capability declaration must cover every field that DEPENDS on tri-state.

WHY A DERIVATION AND NOT A LIST

``_mapper_capabilities.REQUIRED_TRI_STATE`` is the one place this package says
which upstream fields must be able to answer "I could not tell". A hand-written
list is exactly the thing that goes stale, and this repository has the receipt:
``test_streamlit_page_imports`` mirrored three of page 1's nine imports, nobody
updated it for three releases, and the deployed app raised ImportError on a
public URL while that test stayed green.

So the set of fields NEEDING a declaration is derived from the adapter's own
source. Every field the adapter routes through ``_prefer_determinate`` is, by
construction, a field whose ``None`` carries meaning -- that helper exists
precisely to distinguish "the mapper could not determine this" from "the mapper
determined False". A field passed through it while typed ``bool`` upstream is
the S2 defect exactly: the guard runs, ``False is None`` is ``False``, and the
fabricated negative sails through.

THIS IS THE CLASS, NOT THE SITE. ``is_non_metro`` was the field that broke.
``is_high_migration_rural`` and ``is_opportunity_zone`` go through the same
helper and would break the same way. The next one added is covered on the run
after it is written, without anybody remembering.

FAILS CLOSED. An empty derivation errors -- if the adapter stops calling
``_prefer_determinate``, or renames it, this gate is checking nothing and says
so rather than passing.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

import nmtcapp.integrations.nmtc_mapper_adapter as adapter_mod
from nmtcapp.integrations._mapper_capabilities import (
    CAPABILITY_FLOOR,
    MapperCapabilityError,
    REQUIRED_TRI_STATE,
    _renders_as_optional,
    assert_mapper_capabilities,
)

_ADAPTER_SOURCE = Path(adapter_mod.__file__)
_GUARD = "_prefer_determinate"


def _fields_routed_through_the_guard() -> set:
    """Fields passed as ``_prefer_determinate(result.<field>, ...)``.

    The first positional argument is the mapper's answer; that is the one whose
    ``None`` has to be reachable. The second is the CDE's declaration and is
    irrelevant here.
    """
    tree = ast.parse(_ADAPTER_SOURCE.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if name != _GUARD or not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.Attribute):
            found.add(first.attr)
    return found


ROUTED = _fields_routed_through_the_guard()


def test_the_derivation_is_not_empty():
    """An empty derivation would make the gate below vacuous."""
    assert ROUTED, (
        f"derived no {_GUARD}() call sites from {_ADAPTER_SOURCE.name}. The "
        "adapter no longer routes mapper answers through that guard, or it "
        "was renamed -- either way this gate is checking nothing. Fix the "
        "derivation; do not delete it."
    )


def test_every_tri_state_dependent_field_is_declared():
    """THE GATE. A field that needs None to mean something must be declared.

    Without this, adding a fourth ``_prefer_determinate`` field silently
    inherits the S2 defect: the guard appears to protect it, and does not,
    because nothing checks that the upstream type can produce ``None`` at all.
    """
    undeclared = sorted(ROUTED - set(REQUIRED_TRI_STATE))
    assert not undeclared, (
        f"{len(undeclared)} field(s) are routed through {_GUARD}() but are not "
        "declared in _mapper_capabilities.REQUIRED_TRI_STATE:\n\n"
        + "\n".join(f"  {name}" for name in undeclared)
        + f"\n\n{_GUARD}() only distinguishes 'could not determine' from "
        "'determined False' when the upstream field can actually BE None. If "
        "it is typed bool upstream, the guard runs, False is not None, and a "
        "fabricated negative passes straight through -- which is the 1.4.1 S2 "
        "defect. Declare the field with what it means, so "
        "assert_mapper_capabilities() checks it at runtime."
    )


def test_no_declaration_is_dead():
    """A declaration for a field nothing reads is a ruling that guards nothing."""
    dead = sorted(set(REQUIRED_TRI_STATE) - ROUTED)
    assert not dead, (
        f"REQUIRED_TRI_STATE declares {dead}, which the adapter no longer "
        f"routes through {_GUARD}(). Remove the declaration, or restore the "
        "read -- a list that only grows stops describing the code."
    )


def test_every_declaration_states_what_the_field_means():
    """The error message is the whole product here; an empty reason wastes it."""
    thin = sorted(
        name for name, meaning in REQUIRED_TRI_STATE.items()
        if not meaning or len(meaning) < 40
    )
    assert not thin, (
        f"{thin} have no usable explanation. A CDE hitting this error at "
        "11pm needs to know what the field is and why a False answer is "
        "wrong, not just its name."
    )


def test_the_assertion_passes_against_the_installed_mapper():
    """The floor and the runtime check must agree on the installed tree."""
    assert_mapper_capabilities()


def test_the_optional_detector_accepts_every_spelling():
    """Three spellings reach this, and reading only one would fail open.

    ``dataclasses.fields()`` returns the annotation as a typing object OR as a
    string, depending on whether the upstream module uses
    ``from __future__ import annotations``. Upstream's choice is not this
    package's to control, and a detector that read only one spelling would
    report a tri-state field as bool-typed (a false alarm) or -- worse, if the
    logic were inverted -- a bool field as tri-state.
    """
    import typing

    for accepted in (
        typing.Optional[bool],
        "Optional[bool]",
        "bool | None",
        "typing.Union[bool, None]",
    ):
        assert _renders_as_optional(accepted), f"rejected {accepted!r}"

    for rejected in (bool, "bool", "str", None, "int"):
        assert not _renders_as_optional(rejected), f"accepted {rejected!r}"


def test_the_error_names_the_remedy_and_the_direction_of_harm():
    """A raise is only better than a degrade if the message does the work.

    The whole argument for failing loudly (see _mapper_capabilities) is that a
    stale install has exactly one remedy and the exception can name it. If the
    message does not, raising is just a worse degrade.
    """
    import dataclasses
    import types

    @dataclasses.dataclass
    class _StaleResult:
        is_non_metro: bool = False
        is_high_migration_rural: bool = False
        is_opportunity_zone: bool = False

    fake_checker = types.ModuleType("nmtcmapper.eligibility.checker")
    fake_checker.EligibilityResult = _StaleResult
    fake_root = types.ModuleType("nmtcmapper")
    fake_root.__version__ = "0.4.3"
    fake_elig = types.ModuleType("nmtcmapper.eligibility")

    import sys
    saved = {name: sys.modules.get(name) for name in
             ("nmtcmapper", "nmtcmapper.eligibility",
              "nmtcmapper.eligibility.checker")}
    sys.modules["nmtcmapper"] = fake_root
    sys.modules["nmtcmapper.eligibility"] = fake_elig
    sys.modules["nmtcmapper.eligibility.checker"] = fake_checker
    try:
        with pytest.raises(MapperCapabilityError) as excinfo:
            assert_mapper_capabilities()
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    message = str(excinfo.value)
    assert "0.4.3" in message, "must name the version actually installed"
    assert f"nmtc-mapper>={CAPABILITY_FLOOR}" in message, "must name the remedy"
    assert "pip install --upgrade" in message, "must be copy-pasteable"
    assert "UNDERSTATES" in message, (
        "must say which DIRECTION the harm runs. 'Your data may be wrong' does "
        "not tell a CDE that the wrongness understates them to a federal "
        "agency, which is the fact that makes stopping worth it."
    )
    for field in REQUIRED_TRI_STATE:
        assert field in message, f"{field} missing from the error"


def test_the_capability_error_is_not_swallowed_by_the_adapter():
    """MapperCapabilityError must not be an NMTCMapperError.

    The adapter converts NMTCMapperError into degraded-but-continuing mode. If
    this exception were a subclass, the guard would be caught by the handler
    three lines below its own call site and turned back into the silent
    behaviour it exists to replace -- green tests, and the defect intact.
    """
    from nmtcmapper import NMTCMapperError

    assert not issubclass(MapperCapabilityError, NMTCMapperError), (
        "MapperCapabilityError is an NMTCMapperError, so "
        "nmtc_mapper_adapter's `except NMTCMapperError` would swallow it into "
        "_mark_unavailable() -- degraded mode, which is exactly the outcome "
        "this check refuses."
    )


def test_the_guard_call_is_outside_the_degrading_try_block():
    """Structure, not convention: the raise must not sit where it can be caught.

    Asserting the subclass relationship above is necessary and not sufficient.
    If ``assert_mapper_capabilities()`` were moved INSIDE the ``try`` that
    degrades, a future broadening of that except clause would silently disarm
    it. This pins the call's position instead.
    """
    tree = ast.parse(_ADAPTER_SOURCE.read_text(encoding="utf-8"))

    called_in_try = False
    called_at_all = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "assert_mapper_capabilities":
            called_at_all = True
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name) \
                    and inner.func.id == "assert_mapper_capabilities":
                called_in_try = True

    assert called_at_all, (
        "the adapter no longer calls assert_mapper_capabilities(), so the "
        "runtime contract is unenforced and only CI would notice a stale "
        "install."
    )
    assert not called_in_try, (
        "assert_mapper_capabilities() is called inside a try block in the "
        "adapter. Move it out: a raise that a neighbouring handler can "
        "convert back into degraded mode is the shape this check exists to "
        "remove."
    )
