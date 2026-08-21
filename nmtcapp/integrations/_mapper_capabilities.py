"""ONE place the nmtc-mapper contract is asserted at RUNTIME, not just in CI.

WHAT THIS CLOSES (1.4.1 S2)

``pyproject.toml`` declares ``nmtc-mapper>=0.5.0``, and
``tests/integrations/test_mapper_contract.py`` proves the floor is real:
``test_the_floor_field_is_tri_state_not_a_bool`` is RED against 0.4.3 and GREEN
against 0.5.0.

Neither of those runs on a CDE's machine.

    pip install nmtc-mapper==0.4.3

into a working install WARNS about the conflict and proceeds. pip's dependency
warning is not an enforcement mechanism and neither is a type annotation. After
that:

    0.4.2 / 0.4.3   is_non_metro: bool            indeterminate -> False
    0.5.0           is_non_metro: Optional[bool]  indeterminate -> None

``_prefer_determinate(False, declared)`` returns ``False``, because ``False`` is
not ``None`` and the guard tests ``is None``. So an unresolvable tract reports
as **not non-metropolitan**, ``geographic_analysis`` reads that as a
determination, and the dollars go into the METROPOLITAN bucket.

**Same code, dependency varied: 100% metropolitan versus 100% not determined.**
No error, no exception, not one changed line in this repository — and the third
bucket that 1.4.0 existed to create silently empties.

WHY THIS RAISES INSTEAD OF DEGRADING, AND THE CASE AGAINST EACH ALTERNATIVE

  DEGRADE THE FIELD TO None ("not determined") -- REJECTED. It produces a
  "not determined" that is INDISTINGUISHABLE FROM A REAL ONE. A CDE would read
  "county status unknown for 100% of QEI" and conclude their geocoding failed,
  not that their library is old. That is precisely the conflation 1.4.0 shipped
  to fix, re-introduced by the guard meant to prevent it.

  DEGRADE THE PIPELINE via ``_mark_unavailable`` -- REJECTED. That status means
  "the CDFI Fund dataset never loaded", a fact about DATA. This is a fact about
  the ENVIRONMENT. Reusing one signal for both tells a CDE their eligibility
  lookup failed when what actually happened is that their install is stale, and
  it yields a complete application document asserting eligibility is
  unavailable — correct, useless, and pointing at the wrong cause.

  RAISE -- CHOSEN. The condition is deterministic: it depends only on which
  version is installed, not on any input, any network call or any tract. It is
  detectable before the first lookup. It has exactly one remedy, and the
  exception names it.

THE CASE AGAINST RAISING, STATED RATHER THAN SKIPPED. A CDE against a deadline
with a pinned old environment can now not run the tool at all, where before
they would have got a complete application with one field silently wrong.

That trade is still right, and the reason is which direction the error runs.
``non_metro_pct`` informs Question 22, whose commitment is a share of QLICIs in
Non-Metropolitan counties. A pipeline reported 100% metropolitan understates the
CDE's own Non-Metropolitan position TO A FEDERAL AGENCY — the false-negative
class ``renderers/_question_25``'s header ranks as the worst error this package
can make. A tool that refuses to start is recoverable with one command. A filing
that understates the applicant is not recoverable at all.

THE GENERAL MECHANISM, BECAUSE A GUARD ON ONE FIELD IS A SITE

The question this had to answer was "is there ONE place dependency capability is
asserted, or is this an ad-hoc check per field?" It is one place:
:data:`REQUIRED_TRI_STATE` below, checked once by
:func:`assert_mapper_capabilities` at the single point of consumption.

And the list is not hand-maintained, because a hand-maintained list drifts —
which is the failure mode ``test_streamlit_page_imports`` demonstrated by
mirroring three of nine imports and going stale for three releases.
``tests/integrations/test_mapper_capabilities.py`` DERIVES the set of fields
that need a declaration by walking the adapter's AST for every field passed
through ``_prefer_determinate``, and fails if any of them is missing here. A new
tri-state-dependent field is therefore a red test until somebody declares it.
"""
from __future__ import annotations

import dataclasses
import typing


class MapperCapabilityError(RuntimeError):
    """The installed nmtc-mapper cannot express an answer this package needs.

    Deliberately NOT an ``NMTCMapperError``: the adapter catches that type and
    converts it into degraded-but-continuing mode, which is the outcome this
    check exists to refuse.
    """


#: Fields whose INDETERMINATE answer must be ``None`` rather than ``False``.
#:
#: A ``bool`` field cannot say "I could not tell". It has to pick, and it picks
#: ``False`` — which every downstream reader takes as a determination. The value
#: beside each name is what the field means, for the error message.
REQUIRED_TRI_STATE = {
    "is_non_metro": (
        "the OMB Non-Metropolitan County determination. Under a bool-typed "
        "mapper every tract it cannot resolve reports as NOT "
        "non-metropolitan, so unverified dollars are counted METROPOLITAN and "
        "the 'not determined' bucket silently empties"
    ),
    "is_high_migration_rural": (
        "the High Migration Rural County determination, which is also a CDE "
        "declaration this package must not overwrite with a fabricated False"
    ),
    "is_opportunity_zone": (
        "the Opportunity Zone designation. The list is 2010-tract-based while "
        "this table and geocoder are 2020-basis, so a non-match and a genuine "
        "non-designation are indistinguishable and only None can say so"
    ),
}

#: The first release whose EligibilityResult types these as Optional[bool].
CAPABILITY_FLOOR = "0.5.0"


def _renders_as_optional(annotation) -> bool:
    """True when a dataclass field annotation admits ``None``.

    Handles both spellings: a real typing object, and the STRING a module using
    ``from __future__ import annotations`` produces. Comparing on the rendered
    form covers both without importing the upstream module's namespace.
    """
    if annotation is None:
        return False
    rendered = annotation if isinstance(annotation, str) else str(annotation)
    return (
        "Optional[bool]" in rendered
        or "bool, NoneType" in rendered
        or "bool | None" in rendered
        or "Union[bool, None]" in rendered
    )


def assert_mapper_capabilities() -> None:
    """Raise unless the INSTALLED nmtc-mapper can express "I could not tell".

    Called once per enrichment, at the point of consumption — not at import
    time. Import-time checks fire in environments that never enrich anything
    (docs builds, ``--help``, a Streamlit page that only reads a CSV), which
    turns a correct guard into a tool that will not start.

    Raises:
        MapperCapabilityError: a required field is absent or typed ``bool``.

    Example::

        assert_mapper_capabilities()   # returns None, or raises
    """
    from nmtcmapper.eligibility.checker import EligibilityResult

    import nmtcmapper
    version = getattr(nmtcmapper, "__version__", "unknown")

    annotations = {f.name: f.type for f in dataclasses.fields(EligibilityResult)}

    absent, bool_typed = [], []
    for field, meaning in REQUIRED_TRI_STATE.items():
        if field not in annotations:
            absent.append(f"  {field} — ABSENT. {meaning}")
        elif not _renders_as_optional(annotations[field]):
            bool_typed.append(
                f"  {field} — declared {annotations[field]!r}, not "
                f"Optional[bool]. {meaning}"
            )

    if not absent and not bool_typed:
        return

    raise MapperCapabilityError(
        f"installed nmtc-mapper {version} cannot express an indeterminate "
        "answer for "
        f"{len(absent) + len(bool_typed)} field(s) this package relies on.\n\n"
        + "\n".join(absent + bool_typed)
        + "\n\nA bool-typed field cannot say 'I could not determine this'. It "
        "returns False, and every reader downstream treats False as a "
        "DETERMINATION — so a tract the mapper could not resolve is silently "
        "counted as a negative finding rather than as unknown.\n\n"
        "THIS IS NOT DEGRADED, IT IS WRONG, AND IT WOULD BE WRONG IN THE "
        "DIRECTION THAT UNDERSTATES YOUR PIPELINE to the CDFI Fund.\n\n"
        f"FIX: pip install --upgrade 'nmtc-mapper>={CAPABILITY_FLOOR}'\n\n"
        "pyproject.toml already declares that floor. If you reached this "
        "message, something installed a lower version over it — pip warns "
        "about the conflict and proceeds anyway, which is why this check "
        "exists at runtime and not only in CI."
    )
