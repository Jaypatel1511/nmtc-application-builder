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
    assert touching == ["integrations/_mapper_capabilities.py",
                        "integrations/nmtc_mapper_adapter.py"], (
        f"another module now touches nmtc-mapper: {touching}. This contract "
        "test only introspects the adapter, and its AST walk cannot follow a "
        "result passed into a helper. Extend the derivation to cover the new "
        "module, or bring the read back into the adapter."
    )
    # _mapper_capabilities JOINED THE SET IN 1.5.0 S2, and it does not widen
    # the hole this test guards. The hole is a RESULT OBJECT passed into a
    # helper that reads attributes off its own parameter, which the AST walk
    # cannot follow. _mapper_capabilities never receives an EligibilityResult:
    # it introspects the CLASS with dataclasses.fields() and reads annotations,
    # so there is no instance and no attribute access to miss. Its own fields
    # are covered by tests/integrations/test_mapper_capabilities.py, which
    # derives them from the adapter rather than from a list.


#: The field the 1.4.0 floor exists for, and the version that first has it.
_CONTRACT_FLOOR = "0.5.0"
_FLOOR_FIELD = "is_non_metro"


def _version_tuple(version: str) -> tuple:
    """``"0.6.1"`` -> ``(0, 6, 1)``, for ordering against ``_CONTRACT_FLOOR``.

    ONLY EVER USED TO CHOOSE A FAILURE MESSAGE, never to decide whether a gate
    passes, so it does not need to be PEP 440 and deliberately does not import
    ``packaging`` to pretend otherwise. A version it cannot parse sorts as
    ``(-1,)`` — below every real release — which routes an unknown version to
    the "check your install" wording rather than to the "upstream regressed"
    wording. That is the right way round: an unparseable version string is
    itself a reason to look at the install.

    Example::

        _version_tuple("0.6.1") >= _version_tuple("0.5.0")   # True
    """
    parts = []
    for chunk in version.split("."):
        digits = ""
        for char in chunk:
            if not char.isdigit():
                break
            digits += char
        if not digits:
            return (-1,)
        parts.append(int(digits))
    return tuple(parts) if parts else (-1,)


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
    """The field must ADMIT ``None``. THIS IS WHY THE FLOOR IS 0.5.0.

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

    THE CHECK IS ON THE RESOLVED TYPE, NOT ON HOW IT IS SPELLED (1.6.2 R2)

    Through 1.6.2 this gate asserted the SUBSTRING ``"Optional[bool]"`` against
    ``dataclasses.fields(...)[i].type``. That is an assertion about typography,
    and typography is not stable across interpreters. nmtc-mapper 0.6.1 writes
    ``is_non_metro: Optional[bool]`` at ``eligibility/checker.py`` with no
    ``from __future__ import annotations``, and the IDENTICAL declaration
    renders:

        Python 3.10.12   ``typing.Optional[bool]``   — gate passed
        Python 3.14.7    ``bool | None``             — gate FAILED

    Both measured, on those two interpreters, against the same installed
    0.6.1. PEP 649 builds the annotation lazily on 3.14 and normalises the
    union to its ``|`` form. The library did not change and the floor was not
    violated: a correct dependency went red on the maintainer's 3.14 machine
    while CI stayed green on an older one. That is a gate reporting the
    renderer, not the contract.

    The PROPERTY the floor rests on was never the spelling. It is *can this
    field say ``None``* — can the mapper report "I could not determine this"
    instead of being forced to report "no". So the annotation is RESOLVED with
    ``typing.get_type_hints`` and the union's arguments are inspected for
    ``bool`` and ``NoneType``. That answer is identical on every interpreter
    and under every spelling: ``Optional[bool]``, ``bool | None`` and the
    stringised ``"Optional[bool]"`` a PEP 563 module produces all resolve to a
    union over ``bool`` and ``NoneType``, while a plain ``bool`` resolves to a
    bare class whose ``get_args`` is empty — the 0.4.3 shape this gate exists
    to reject. Verified on 3.10.12 and 3.14.7 for all four cases.

    ``get_type_hints`` is also what handles the stringised form properly. The
    old code special-cased it by comparing strings, which works only while the
    string happens to be spelled the way the comparison expects; resolving it
    removes the coincidence.

    RESOLUTION FAILURE IS A THIRD OUTCOME AND IS REPORTED AS ITSELF. See the
    ``except`` branch below: "the annotation would not evaluate" is not
    evidence that the field is a plain ``bool``, and must not be reported as
    though it were.
    """
    import typing
    from nmtcmapper.eligibility.checker import EligibilityResult

    import nmtcmapper
    version = getattr(nmtcmapper, "__version__", "unknown")

    declared = {
        f.name: f.type for f in dataclasses.fields(EligibilityResult)
    }[_FLOOR_FIELD]

    # NOT AN ASSERTION FAILURE DRESSED AS THE DEFECT. get_type_hints evaluates
    # the annotation in the DEFINING MODULE's namespace and raises when a name
    # there is unresolvable (a stringised annotation naming something imported
    # only under TYPE_CHECKING, for one). That says the annotation is
    # unreadable. It says NOTHING about whether the field is tri-state, so
    # this branch refuses to answer rather than guessing.
    try:
        resolved = typing.get_type_hints(EligibilityResult)[_FLOOR_FIELD]
    except Exception as exc:                        # noqa: BLE001 — see above
        raise AssertionError(
            f"could not RESOLVE EligibilityResult.{_FLOOR_FIELD} on installed "
            f"nmtc-mapper {version}: {type(exc).__name__}: {exc}\n\n"
            f"The raw annotation is {declared!r}.\n\n"
            "THIS IS A RESOLUTION FAILURE, NOT A FINDING ABOUT THE FIELD. "
            "This gate cannot tell you whether the field admits None, so it "
            "is not telling you. Do NOT change the installed version and do "
            "NOT touch pyproject.toml's floor on the strength of this "
            "message. Find out why the annotation does not evaluate in "
            "nmtcmapper.eligibility.checker's namespace — that is the "
            "question this raised."
        ) from exc

    args = typing.get_args(resolved)
    admits_none = bool(args) and bool in args and type(None) in args

    # Whether the INSTALLED version is already at or above the floor decides
    # which of two different things went wrong, and therefore what the reader
    # should do. Telling someone to upgrade a package that is already current
    # sends them to do nothing, twice.
    at_or_above_floor = _version_tuple(version) >= _version_tuple(_CONTRACT_FLOOR)

    if at_or_above_floor:
        remedy = (
            f"The installed {version} is AT OR ABOVE the {_CONTRACT_FLOOR} "
            "floor, so this is NOT an old-version problem and upgrading will "
            "not fix it. Upstream has REGRESSED the field to two states in a "
            "release that is supposed to have three — the same class of "
            "event as 0.5.0 dropping is_nmtc_native_area. Read that release's "
            "changelog and raise it with the mapper, then decide whether this "
            "package can still enrich against it at all. Do not lower "
            "pyproject.toml's floor: a lower version has the same defect."
        )
    else:
        remedy = (
            f"The installed {version} is BELOW the {_CONTRACT_FLOOR} floor "
            "pyproject.toml declares, which is exactly the version range "
            "where this field is a plain bool. Something installed it over "
            "the declared floor — pip warns about that conflict and proceeds "
            f"anyway. FIX: pip install --upgrade 'nmtc-mapper>="
            f"{_CONTRACT_FLOOR}'. Do not lower the floor to accommodate it."
        )

    assert admits_none, (
        f"installed nmtc-mapper {version} declares "
        f"EligibilityResult.{_FLOOR_FIELD} as {resolved!r}, which does NOT "
        f"admit None — it is a two-state field, so the mapper has no value "
        f"left to mean 'not determined'.\n\n"
        f"(raw annotation {declared!r}; resolved args {args!r}. The check is "
        f"on the resolved type, so this is not a spelling difference — see "
        f"this test's docstring.)\n\n"
        "geographic_analysis reads False as a DETERMINATION and counts those "
        "dollars metropolitan, so the 'not determined' bucket empties "
        "silently and the non-metropolitan share goes back to being a "
        f"complement.\n\n{remedy}"
    )

    # Pin the premise: Optional[X] IS the union of X and None, whatever the
    # interpreter prints. If this ever stops holding, the predicate above is
    # reading something other than what the docstring says it reads.
    assert typing.get_args(typing.Optional[bool]) == (bool, type(None))


def test_every_double_neutral_matches_the_librarys_own_default():
    """A double's "neutral" must be the LIBRARY's neutral, not a plausible one.

    THE HOLE THIS CLOSES, FOUND BY MUTATION (1.6.2 fix round).
    ``tests/mapper_doubles._NEUTRAL`` gained three entries when nmtc-mapper
    0.6.1 added the OZ 2.0 fields. ``_defaults()`` fails loud on a field with
    NO entry -- that is what stopped the suite and is the mechanism working --
    but it says nothing at all about whether the VALUE chosen is neutral.
    Measured: flipping ``is_oz2_nomination_eligible`` to ``False`` and running
    the whole suite reddened **nothing**.

    That is the expensive direction. ``is_opportunity_zone``'s ``False`` never
    occurs upstream; ``is_oz2_nomination_eligible``'s ``False`` is, in the
    library's own words, "a real published fact about 60,197 tracts". A double
    answering ``False`` where the library answers ``None`` asserts a published
    federal negative about a fixture address -- a fabricated negative, which is
    the defect class ``mapper_doubles`` exists to refuse, produced by the
    module written to refuse it.

    THE ANSWER IS READ OFF THE INSTALLED LIBRARY, NOT LISTED HERE. Every field
    ``EligibilityResult`` declares WITH A DEFAULT has already had its neutral
    chosen upstream, by the author who knows what the field means; the double
    must agree with it. Fields with no default are the double's own call and
    are not constrained here -- there is nothing upstream to compare them to.

    This is the same shape as the contract tests above: introspect the library,
    do not restate it.
    """
    import dataclasses

    from nmtcmapper.eligibility.checker import EligibilityResult

    from tests.mapper_doubles import _NEUTRAL

    disagree = []
    checked = 0
    for field in dataclasses.fields(EligibilityResult):
        if field.default is dataclasses.MISSING:
            continue
        checked += 1
        if field.name not in _NEUTRAL:
            continue        # _defaults() already raises on this, loudly
        if _NEUTRAL[field.name] != field.default:
            disagree.append(
                f"{field.name}: the library defaults to "
                f"{field.default!r}; mapper_doubles neutralises to "
                f"{_NEUTRAL[field.name]!r}"
            )

    assert checked, (
        "the installed EligibilityResult declares NO field with a default, so "
        "this gate compared nothing. Either the library changed shape or the "
        "introspection did; establish which before deleting this line."
    )
    assert not disagree, (
        f"{len(disagree)} double neutral(s) disagree with the installed "
        "nmtc-mapper's own default:\n  " + "\n  ".join(disagree) + "\n\n"
        "A default is the library author's statement of what the field says "
        "when nothing was determined. A double that answers something else "
        "answers CONFIDENTLY where the real package abstains, and every test "
        "built on it is then validating the mock. Change the neutral, not "
        "this gate."
    )
