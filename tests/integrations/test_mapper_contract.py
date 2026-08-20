"""Contract test: every nmtc-mapper attribute the adapter reads must exist.

WHY THIS EXISTS

nmtc-mapper 0.5.0 dropped ``EligibilityResult.is_nmtc_native_area``. The
adapter read that field on every geocoded project, so `nmtcapp analyze`
raised AttributeError on any real pipeline the moment 0.5.0 resolved — and
the declared floor ``nmtc-mapper>=0.4.2`` resolves straight to it.

The whole suite stayed green through that, because the test doubles in
tests/integrations/test_no_fabrication.py and
tests/renderers/test_partial_unverified_exports.py constructed
``is_nmtc_native_area=False`` themselves. **The tests validated the mock,
not the library.** tests/test_no_fabricated_output.py cannot catch it either:
it renders from pre-enriched pipelines and never touches a real
EligibilityResult.

So this test introspects the INSTALLED library and asserts the adapter's
actual reads resolve against it. It is the gate that fires the moment an
upstream release removes a field, rather than a CDE discovering it.

The attribute list is DERIVED FROM THE ADAPTER SOURCE by AST walk, never
hand-copied — a hand-maintained list drifts silently, which is the same
failure mode as the doubles. An empty derived list is an error, not a pass.
"""
from __future__ import annotations

import ast
import dataclasses
import inspect
import re
from pathlib import Path

import pytest

import nmtcapp.integrations.nmtc_mapper_adapter as adapter_mod


_ADAPTER_SOURCE = Path(adapter_mod.__file__)

# Local variable names the adapter binds to each upstream object. If the
# adapter is refactored to use different names, the derivation below returns
# an empty set and the test ERRORS rather than silently checking nothing.
_RESULT_VAR = "result"   # bound from mapper.check_address(...)
_MAPPER_VAR = "mapper"   # bound from NMTCMapper()


def _alias_names(tree: ast.AST, var_name: str) -> set:
    """Local names bound to ``var_name`` by simple assignment, transitively.

    THE HOLE THIS CLOSES, reproduced before it was fixed: the derivation used
    to match only attribute access whose base was literally the Name
    ``result``. One intermediate binding defeated it —

        r = result
        project.is_us_territory = r.is_nmtc_native_area

    — and that passed the contract test (12 passed) and the denylist gate
    (151 passed) while ``enrich_pipeline_eligibility`` raised the exact
    AttributeError this file exists to catch. Aliased reads of
    ``is_native_area`` specifically were still caught, but only by the
    field-specific regex in test_native_area_is_not_read_from_the_mapper —
    protection for one field, not for the contract.

    Also resolves ``for x in (result,)`` and walrus bindings. It does NOT
    follow a result passed as an argument into another function; see
    test_derivation_boundary_is_documented below.

    Example::

        # r = result  ->  {'result', 'r'}
    """
    names = {var_name}
    # Iterate to a fixed point so r = result; q = r resolves both.
    for _ in range(8):
        before = len(names)
        for node in ast.walk(tree):
            value = getattr(node, "value", None)
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)):
                targets = [node.target]
            if targets and isinstance(value, ast.Name) and value.id in names:
                for t in targets:
                    if isinstance(t, ast.Name):
                        names.add(t.id)
        if len(names) == before:
            break
    return names


def _derive_reads(var_name: str) -> set:
    """Attribute names read off ``var_name`` — or any local alias of it.

    Catches plain attribute access (``result.tract_id``), the defensive
    ``getattr(mapper, "data_source", None)`` form the adapter uses for its
    provenance check, f-string interpolations (ast.walk descends into
    FormattedValue), and reads through a local alias (see _alias_names).
    """
    tree = ast.parse(_ADAPTER_SOURCE.read_text(encoding="utf-8"))
    names = _alias_names(tree, var_name)
    found = set()

    for node in ast.walk(tree):
        # result.tract_id  /  mapper.check_address  /  r.tract_id
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id in names:
                found.add(node.attr)
        # getattr(mapper, "data_source", None)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "getattr" and len(node.args) >= 2:
                target, attr = node.args[0], node.args[1]
                if (isinstance(target, ast.Name) and target.id in names
                        and isinstance(attr, ast.Constant)
                        and isinstance(attr.value, str)):
                    found.add(attr.value)

    return found


RESULT_READS = sorted(_derive_reads(_RESULT_VAR))
MAPPER_READS = sorted(_derive_reads(_MAPPER_VAR))


def test_result_read_derivation_is_not_empty():
    """An empty derived list would make every assertion below vacuous."""
    assert RESULT_READS, (
        f"derived no EligibilityResult attribute reads from {_ADAPTER_SOURCE.name} "
        f"— the adapter no longer binds its result to {_RESULT_VAR!r}, so this "
        "contract test is checking nothing. Fix the derivation, do not delete it."
    )


def test_mapper_read_derivation_is_not_empty():
    assert MAPPER_READS, (
        f"derived no NMTCMapper attribute reads from {_ADAPTER_SOURCE.name} "
        f"— the adapter no longer binds its mapper to {_MAPPER_VAR!r}, so this "
        "contract test is checking nothing. Fix the derivation, do not delete it."
    )


@pytest.mark.parametrize("attr", RESULT_READS, ids=RESULT_READS)
def test_eligibility_result_has_attribute(attr):
    """Every field the adapter reads must exist on the INSTALLED library."""
    from nmtcmapper.eligibility.checker import EligibilityResult

    fields = {f.name for f in dataclasses.fields(EligibilityResult)}
    import nmtcmapper
    version = getattr(nmtcmapper, "__version__", "unknown")

    assert attr in fields, (
        f"nmtc_mapper_adapter reads EligibilityResult.{attr}, which does NOT "
        f"exist in the installed nmtc-mapper {version}. Every geocoded project "
        f"would raise AttributeError. Installed fields: {sorted(fields)}"
    )


@pytest.mark.parametrize("attr", MAPPER_READS, ids=MAPPER_READS)
def test_nmtc_mapper_has_attribute(attr):
    """Every NMTCMapper attribute/method the adapter reads must exist.

    Checked without instantiating: NMTCMapper() downloads the CDFI Fund
    eligibility workbook. Class-level attributes and methods answer via
    hasattr; instance attributes assigned in __init__ (data_source) are
    found by reading the class source.
    """
    import nmtcmapper
    from nmtcmapper import NMTCMapper

    version = getattr(nmtcmapper, "__version__", "unknown")

    if hasattr(NMTCMapper, attr):
        return

    try:
        src = inspect.getsource(NMTCMapper)
    except (OSError, TypeError):  # pragma: no cover - source always available
        pytest.fail(
            f"cannot verify NMTCMapper.{attr} on nmtc-mapper {version}: "
            "class source unavailable and attribute absent from the class"
        )

    assigned = re.search(rf"self\.{re.escape(attr)}\s*(?::[^=]+)?=", src)
    assert assigned, (
        f"nmtc_mapper_adapter reads NMTCMapper.{attr}, which is neither a "
        f"class attribute nor assigned in __init__ in the installed "
        f"nmtc-mapper {version}."
    )


def test_native_area_is_not_read_from_the_mapper():
    """is_native_area is the CDE's declaration; enrichment must not touch it.

    nmtc-mapper carried is_nmtc_native_area at 0.4.2/0.4.3 but it was always
    False, so reading it overwrote a CDE's correctly-supplied True with a
    fabricated negative — and 0.5.0 removed it entirely. Neither the field
    nor the project attribute may be assigned during enrichment again.
    """
    source = _ADAPTER_SOURCE.read_text(encoding="utf-8")
    code_lines = [
        line for line in source.splitlines()
        if not line.lstrip().startswith("#")
    ]
    code = "\n".join(code_lines)

    assert "is_nmtc_native_area" not in RESULT_READS, (
        "the adapter reads is_nmtc_native_area again — the field does not "
        "exist in nmtc-mapper >= 0.5.0 and was always False before that"
    )
    assert not re.search(r"project\.is_native_area\s*=", code), (
        "enrichment assigns project.is_native_area again — that field is "
        "supplied by the CDE (CSV column 'native_area' / upload column "
        "'Native Area (Y/N)') and must not be overwritten"
    )


def test_alias_reads_are_derived():
    """A read through a local alias must be visible to the derivation.

    Guards the fix for the hole described in _alias_names. Without it,
    `r = result; r.<field>` is invisible and a removed upstream field passes
    every gate while analyze raises AttributeError on the first real project.
    """
    tree = ast.parse(
        "def f(result):\n"
        "    r = result\n"
        "    q = r\n"
        "    return q.some_removed_field\n"
    )
    assert "r" in _alias_names(tree, "result")
    assert "q" in _alias_names(tree, "result"), "transitive aliases not resolved"


def test_derivation_boundary_is_documented():
    """State what the AST walk still cannot see, rather than implying it sees all.

    NOT covered: a result passed as an ARGUMENT into another function, which
    then reads an attribute off its own parameter —

        def _na(res): return res.is_nmtc_native_area   # invisible here

    That is currently unreachable: nmtc_mapper_adapter.py is the only module
    in the package that touches nmtcmapper, and it defines no such helper.
    This test pins that premise, so the boundary becomes false loudly rather
    than silently if someone adds one.
    """
    import pathlib
    import nmtcapp

    root = pathlib.Path(nmtcapp.__file__).parent
    touching = sorted(
        str(p.relative_to(root))
        for p in root.rglob("*.py")
        if "nmtcmapper" in p.read_text(encoding="utf-8")
    )
    assert touching == ["integrations/nmtc_mapper_adapter.py"], (
        f"another module now touches nmtc-mapper: {touching}. This contract "
        "test only introspects the adapter, and its AST walk cannot follow a "
        "result passed into a helper. Extend the derivation to cover the new "
        "module, or bring the read back into the adapter."
    )


#: The field the 1.4.0 floor exists for, and the version that first has it.
_CONTRACT_FLOOR = "0.5.0"
_FLOOR_FIELD = "is_non_metro"


def test_the_floor_field_is_present():
    """``is_non_metro`` must exist on the installed EligibilityResult.

    THIS IS NOT THE REASON THE FLOOR MOVED, and saying so is the point of
    writing it down. ``is_non_metro`` exists in every nmtc-mapper back to
    0.3.4 — measured, by installing 0.3.4, 0.4.0, 0.4.1, 0.4.2, 0.4.3 and
    0.5.0 and introspecting the dataclass in each. The plan for this round
    asserted the field was new at 0.5.0; it is not, and a floor defended on
    that ground would have been a true-sounding sentence about a false fact.

    So this test guards presence, which the old floor already gave us, and
    ``test_the_floor_field_is_tri_state_not_a_bool`` below guards the thing
    that actually changes at 0.5.0. Both are kept: presence is what the
    adapter needs not to raise, and tri-state is what the share needs to be
    correct. They fail with different messages because they have different
    causes.
    """
    import nmtcmapper
    from nmtcmapper.eligibility.checker import EligibilityResult

    version = getattr(nmtcmapper, "__version__", "unknown")
    fields = {f.name for f in dataclasses.fields(EligibilityResult)}

    assert _FLOOR_FIELD in fields, (
        f"installed nmtc-mapper {version} has no "
        f"EligibilityResult.{_FLOOR_FIELD}. Every geocoded project would raise "
        f"AttributeError in nmtc_mapper_adapter._enrich_via_api. The field has "
        f"been present since 0.3.4, so this failure means UPSTREAM REMOVED IT "
        f"— which is what happened to is_nmtc_native_area at 0.5.0. Do not "
        f"lower the floor to get it back; find out what replaced it. "
        f"Installed fields: {sorted(fields)}"
    )


def test_the_floor_field_is_tri_state_not_a_bool():
    """``Optional[bool]``, not ``bool``. THIS IS WHY THE FLOOR IS 0.5.0.

    Measured across every installable release:

    ==============  =============================  =====================
    version         annotation                     indeterminate branch
    ==============  =============================  =====================
    0.4.2, 0.4.3    ``is_non_metro: bool``         ``False``
    0.5.0           ``is_non_metro: Optional[bool]``  ``None``
    ==============  =============================  =====================

    Under 0.4.3 a tract the mapper could not resolve reports as **not
    non-metropolitan**, and ``intelligence/geographic_analysis`` reads that as
    a determination and puts the dollars in the METROPOLITAN bucket. The third
    bucket silently empties and every unverified dollar is counted
    metropolitan again — which is precisely the defect 1.4.0 R2 removed from
    the twelve-state list, re-entering through the dependency, with no error
    raised and not one changed line in this repository.

    **RED against nmtc-mapper 0.4.3, GREEN against 0.5.0.** Verified by
    installing each and running this file. It is the assertion that makes
    ``nmtc-mapper>=0.5.0`` a floor with a reason rather than a preference.
    """
    import typing
    from nmtcmapper.eligibility.checker import EligibilityResult

    annotations = {f.name: f.type for f in dataclasses.fields(EligibilityResult)}
    declared = annotations[_FLOOR_FIELD]
    # Dataclass field types may arrive as a string under `from __future__
    # import annotations`; compare on the rendered form so both spellings work.
    rendered = declared if isinstance(declared, str) else str(declared)

    import nmtcmapper
    version = getattr(nmtcmapper, "__version__", "unknown")

    assert "Optional[bool]" in rendered or "bool, NoneType" in rendered, (
        f"installed nmtc-mapper {version} declares "
        f"EligibilityResult.{_FLOOR_FIELD} as {rendered!r}, not Optional[bool]."
        f"\n\nThis is almost certainly a mapper older than "
        f"{_CONTRACT_FLOOR}, where the field is a plain bool and the "
        f"indeterminate branch returns False. geographic_analysis reads False "
        f"as a DETERMINATION and counts those dollars metropolitan, so the "
        f"'not determined' bucket empties silently and the non-metropolitan "
        f"share goes back to being a complement. Raise the installed version; "
        f"do not lower pyproject.toml's floor."
    )
    assert typing.Optional[bool] == typing.Union[bool, None]  # pin the premise
