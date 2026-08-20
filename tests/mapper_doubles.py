"""Test doubles for nmtc-mapper results, BUILT FROM THE REAL DATACLASS.

WHY THIS MODULE EXISTS (1.4.0 R1)

Two test files hand-built ``types.SimpleNamespace`` stand-ins for
``EligibilityResult``, each listing the fields the adapter happened to read at
the time it was written. That is the same failure mode
``tests/integrations/test_mapper_contract.py`` was created to catch, one layer
down: **the tests validate the mock, not the library.**

It has now fired twice in this package, in both directions.

  * 0.5.0 REMOVED ``is_nmtc_native_area`` and the whole suite stayed green,
    because the doubles constructed the field themselves. ``nmtcapp analyze``
    raised ``AttributeError`` on the first real project.
  * 1.4.0 ADDED a read of ``is_non_metro`` and eight tests errored with
    ``'types.SimpleNamespace' object has no attribute 'is_non_metro'`` — noise
    from the doubles, not a finding about the code.

The second is the cheap direction and the first is the expensive one, but they
are the same defect: a double whose field list is a copy of a contract rather
than the contract itself.

So the doubles are built by instantiating the INSTALLED ``EligibilityResult``.
A field added upstream arrives here with a documented default and no test
changes; a field removed upstream makes ``_defaults()`` raise a ``TypeError``
naming it, which is a louder and earlier signal than an ``AttributeError``
inside the adapter.

WHAT THIS DELIBERATELY DOES NOT DO: it does not relax the doubles into
``MagicMock``. A ``MagicMock`` answers every attribute, so a read of a field
that upstream deleted would return a Mock and flow into a project as a
plausible-looking value. The point is a real dataclass with real fields.
"""
from __future__ import annotations

import dataclasses

from nmtcmapper.eligibility.checker import EligibilityResult


#: Values for every field the double does not care about. Chosen to be
#: INDETERMINATE wherever the type allows, so a double that forgets to set a
#: field it does care about produces "unknown" rather than a confident wrong
#: answer. ``distress_level`` is a plain ``str`` upstream and its indeterminate
#: sentinel is the string "unknown", which the adapter maps to ``None``.
_NEUTRAL = {
    "address": "100 Main St, Springfield, IL",
    "tract_id": None,
    "nmtc_eligible": None,
    "distress_level": "unknown",
    "poverty_rate": None,
    "ami_ratio": None,
    "unemployment_rate": None,
    "is_non_metro": None,
    "is_high_migration_rural": None,
    "severe_distress": None,
    "deep_distress": None,
    "geocode_success": False,
    "is_opportunity_zone": None,
    "tract_found": True,
}


def _defaults() -> dict:
    """Neutral values for exactly the installed dataclass's fields.

    Raises if the installed library has a field this module does not know
    about — which is the signal that a new upstream field needs a considered
    neutral value, not a silently-defaulted one.
    """
    names = [f.name for f in dataclasses.fields(EligibilityResult)]
    unknown = [n for n in names if n not in _NEUTRAL]
    if unknown:
        raise TypeError(
            f"installed nmtc-mapper's EligibilityResult has field(s) "
            f"{unknown} that tests/mapper_doubles.py has no neutral value "
            "for. Add one — choosing the INDETERMINATE value for its type — "
            "rather than letting the doubles default it to something "
            "confident."
        )
    return {n: _NEUTRAL[n] for n in names}


def eligibility_result(**overrides) -> EligibilityResult:
    """A real ``EligibilityResult``, neutral except where overridden.

    Example::

        eligibility_result(geocode_success=True, tract_id="17031838200",
                           nmtc_eligible=True, distress_level="deep")
    """
    fields = {f.name for f in dataclasses.fields(EligibilityResult)}
    unexpected = set(overrides) - fields
    if unexpected:
        raise TypeError(
            f"EligibilityResult has no field(s) {sorted(unexpected)} in the "
            "installed nmtc-mapper. A double may not invent a field the "
            "library does not have — that is how a read of a removed field "
            "passed every gate in this package once already."
        )
    return EligibilityResult(**{**_defaults(), **overrides})


def ok_result(address: str, tract: str, distress: str, **overrides):
    """A geocoded, tract-found, eligible result.

    ``is_non_metro`` defaults to ``None`` (not determined) rather than
    ``False``. A double that quietly asserted "metropolitan" for every project
    would make the three-way split in intelligence/geographic_analysis look
    two-way in every test that uses it.
    """
    fields = dict(
        address=address, tract_id=tract, geocode_success=True,
        nmtc_eligible=True, distress_level=distress, tract_found=True,
        is_high_migration_rural=False, is_opportunity_zone=False,
    )
    # Overrides win over the "ok" shape, so a caller can build the
    # geocoded-but-tract-absent branch as ok_result(..., tract_found=False)
    # without a second constructor.
    fields.update(overrides)
    return eligibility_result(**fields)


def geocode_failed(address: str, **overrides):
    """The "ineligible"-shaped result nmtc-mapper returns on a geocode miss.

    Mirrors the upstream shape deliberately, including the misleading
    ``nmtc_eligible=False`` / ``distress_level="ineligible"`` pair: the adapter
    must treat this as UNVERIFIED and copy none of it, and a double that
    cleaned the values up would stop testing that.
    """
    fields = dict(
        address=address, tract_id=None, geocode_success=False,
        nmtc_eligible=False, distress_level="ineligible",
        is_high_migration_rural=False, is_opportunity_zone=False,
    )
    fields.update(overrides)
    return eligibility_result(**fields)
