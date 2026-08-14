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


def _derive_reads(var_name: str) -> set:
    """Attribute names read off ``var_name`` anywhere in the adapter.

    Catches both plain attribute access (``result.tract_id``) and the
    defensive ``getattr(mapper, "data_source", None)`` form the adapter uses
    for its provenance check.
    """
    tree = ast.parse(_ADAPTER_SOURCE.read_text(encoding="utf-8"))
    found = set()

    for node in ast.walk(tree):
        # result.tract_id  /  mapper.check_address
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == var_name:
                found.add(node.attr)
        # getattr(mapper, "data_source", None)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "getattr" and len(node.args) >= 2:
                target, attr = node.args[0], node.args[1]
                if (isinstance(target, ast.Name) and target.id == var_name
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
