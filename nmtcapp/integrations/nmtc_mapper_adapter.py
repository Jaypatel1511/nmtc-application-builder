"""Adapter wrapping nmtc-mapper for pipeline eligibility enrichment.

Failure semantics (v1.1.5): eligibility data is either verified live CDFI Fund
data or explicitly UNAVAILABLE/UNVERIFIED. Nothing is ever substituted or
fabricated. When nmtc-mapper cannot load its dataset, the pipeline is marked
``eligibility_data_status = "unavailable"`` and every eligibility field stays
``None``; downstream scoring excludes the eligibility component and labels the
score as partial. A project whose location cannot be geocoded gets
``geocode_success = False`` and stays unverified — it is never assigned a
substitute tract and never treated as ineligible.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nmtcapp.integrations._mapper_capabilities import assert_mapper_capabilities

if TYPE_CHECKING:
    from nmtcapp.core.pipeline import Pipeline

logger = logging.getLogger(__name__)


def enrich_pipeline_eligibility(pipeline: "Pipeline") -> "Pipeline":
    """Populate census tract and distress data on each project via nmtc-mapper.

    Uses live geocoding + the CDFI Fund eligibility dataset. If the dataset
    cannot be loaded (:class:`nmtcmapper.NMTCMapperError`), the pipeline is
    marked degraded — ``pipeline.eligibility_data_status == "unavailable"``
    with the underlying error in ``pipeline.eligibility_data_error`` — and
    eligibility fields remain ``None``. Unexpected exceptions propagate.

    Fields populated on each :class:`~nmtcapp.core.pipeline.PipelineProject`:
    - ``census_tract``
    - ``is_nmtc_eligible``
    - ``distress_level``
    - ``is_high_migration_rural``
    - ``is_opportunity_zone``
    - ``is_non_metro``
    - ``geocode_success``

    ``is_native_area`` is NOT populated here. It is supplied by the CDE via
    the ``native_area`` CSV column / "Native Area (Y/N)" upload column, and
    enrichment must not overwrite it.

    Example::

        enriched = enrich_pipeline_eligibility(pipeline)
        if enriched.eligibility_data_status != "ok":
            print(f"Unavailable: {enriched.eligibility_data_error}")
    """
    projects = list(pipeline)
    if not projects:
        return pipeline

    # If all projects already enriched (e.g. Pipeline.sample()), skip API call.
    #
    # This branch used to return without touching eligibility_data_status,
    # which Pipeline.__init__ sets to "unenriched". Every downstream surface
    # tests `status != "ok"`, so a fully pre-enriched pipeline rendered the
    # whole application behind "ELIGIBILITY DATA UNAVAILABLE — reason unknown"
    # — a false statement, and "reason unknown" was literally true only
    # because the code never recorded one.
    #
    # The status is now explicit AND distinct from "ok". These values did not
    # come from a live CDFI Fund lookup in this run, so claiming "ok" would
    # assert a provenance the run cannot support; downstream treats any
    # non-"ok" status as degraded, which is the conservative direction.
    if all(p.is_enriched for p in projects):
        logger.debug("Pipeline already enriched — skipping nmtc-mapper call")
        # Only fill in a status that was never set. Pipeline.sample() stamps
        # "ok" at construction and documents itself as the one path allowed to
        # vouch for its own provenance (core/pipeline.py) — clobbering that
        # would push every offline demo and fixture into degraded mode.
        if pipeline.eligibility_data_status == "unenriched":
            pipeline.eligibility_data_status = "pre_enriched"
            pipeline.eligibility_data_error = (
                "every project arrived with eligibility already populated, so "
                "no CDFI Fund lookup was performed in this run — these values "
                "were supplied by the caller and are not tool-verified"
            )
        return pipeline

    from nmtcmapper import NMTCMapper, NMTCMapperError

    # THE DEPENDENCY CONTRACT, ASSERTED AT THE POINT OF CONSUMPTION (1.5.0 S2).
    #
    # Deliberately BEFORE NMTCMapper() and outside the try/except below. Two
    # reasons, and the second is the one that matters:
    #
    #   1. It needs no dataset, no network and no tract, so failing first
    #      costs nothing and reports the real cause instead of whatever the
    #      loader happens to say afterwards.
    #   2. MapperCapabilityError is NOT an NMTCMapperError, so the except
    #      clause below cannot swallow it into degraded mode. A guard that a
    #      neighbouring handler converts back into "continue quietly" is the
    #      shape this whole check exists to remove; keeping it outside the
    #      block is what makes that structural rather than a convention.
    #
    # It RAISES rather than degrading. See _mapper_capabilities for the
    # argument, including the case against each degrade path and the cost of
    # raising.
    assert_mapper_capabilities()

    try:
        mapper = NMTCMapper()
    except NMTCMapperError as exc:
        return _mark_unavailable(pipeline, str(exc))

    # Provenance check (defense-in-depth): only live CDFI Fund data may flow
    # into an application, even if a sample-stamped mapper is injected.
    data_source = getattr(mapper, "data_source", None)
    if data_source != "cdfi_fund":
        return _mark_unavailable(
            pipeline,
            f"eligibility data source is {data_source!r}, not the live CDFI "
            "Fund dataset — refusing to use it for application content",
        )

    _enrich_via_api(projects, mapper, NMTCMapperError)
    pipeline.eligibility_data_status = "ok"
    pipeline.eligibility_data_error = None
    logger.info("nmtc-mapper enrichment complete for %d projects", len(projects))
    return pipeline


def _mark_unavailable(pipeline: "Pipeline", reason: str) -> "Pipeline":
    """Enter degraded mode: eligibility fields stay None, status is explicit."""
    pipeline.eligibility_data_status = "unavailable"
    pipeline.eligibility_data_error = reason
    logger.warning(
        "nmtc-mapper eligibility data unavailable (%s). Eligibility fields "
        "remain unverified; scoring will exclude the eligibility component.",
        reason,
    )
    return pipeline


def _enrich_via_api(projects, mapper, mapper_error: type) -> None:
    """Call nmtc-mapper check_address for each un-enriched project.

    A project whose location cannot be verified (geocode failure or a typed
    mapper error) is marked ``geocode_success = False`` with all eligibility
    fields left ``None`` — unverified, not ineligible, and never a substitute
    tract. Unexpected exceptions propagate.
    """
    for project in projects:
        if project.is_enriched:
            continue
        try:
            result = mapper.check_address(project.full_address)
        except mapper_error as exc:
            logger.warning(
                "Location could not be verified for project %s (%s): %s — "
                "leaving eligibility unverified",
                project.project_id, project.full_address, exc,
            )
            project.geocode_success = False
            continue
        if not result.geocode_success:
            # nmtc-mapper returns an "ineligible"-shaped result on geocode
            # failure; treat it as UNVERIFIED — do not copy those values.
            logger.warning(
                "Location could not be verified for project %s (%s) — "
                "leaving eligibility unverified",
                project.project_id, project.full_address,
            )
            project.geocode_success = False
            continue

        # tract_found is the SECOND indeterminate branch, and the adapter did
        # not read it until 1.2.0. The address geocodes, so geocode_success is
        # True, but the resulting GEOID is absent from the CDFI Fund's 85,395-
        # row universe — a 2010/2020 vintage mismatch or a bad id. nmtc-mapper
        # 0.5.0 returns nmtc_eligible=None and the STRING sentinel
        # distress_level="unknown" there.
        #
        # Copying that sentinel wrote "unknown" over the tool-verified distress
        # field as though it were a determination. _prefer_determinate could
        # not have caught it either: it tests `is None`, and "unknown" is a
        # non-empty string, so it passes straight through. Verified by
        # execution: _prefer_determinate("unknown", "deep") -> "unknown".
        #
        # The right reading of "no row was read for this tract" is the same as
        # a geocode miss: UNVERIFIED. Leave every eligibility field None.
        if not getattr(result, "tract_found", True):
            logger.warning(
                "Project %s geocoded to tract %s, which is absent from the "
                "CDFI Fund eligibility table — leaving eligibility unverified "
                "rather than recording an indeterminate verdict",
                project.project_id, result.tract_id,
            )
            project.geocode_success = True
            continue

        project.geocode_success = True
        project.census_tract = result.tract_id
        project.is_nmtc_eligible = result.nmtc_eligible
        # Defence in depth: never store an indeterminate distress sentinel as
        # though it were a verdict, whatever branch produced it.
        project.distress_level = _determinate_distress(result.distress_level)
        # is_native_area is deliberately NOT set from the mapper result.
        #
        # It is the CDE's own declaration: PipelineProject.is_native_area
        # (core/pipeline.py) is read from the CSV column `native_area`
        # (pipeline.py) and from the "Native Area (Y/N)" upload column
        # (core/upload_handler.py) — column 17 of the shipped template.
        #
        # nmtc-mapper never determined it. At 0.4.2/0.4.3 EligibilityResult
        # carried is_nmtc_native_area but it was ALWAYS False, so this
        # assignment overwrote a CDE's correctly-supplied True with a
        # fabricated negative. 0.5.0 dropped the field outright, which turned
        # the same line into an AttributeError that failed every geocodable
        # project. Deleting the read fixes both: the CDE's declaration stands,
        # and an undeclared project stays None (unverified) rather than False.

        # Both of these are ALSO CDE-supplied CSV columns
        # (`high_migration_rural`, `opportunity_zone`), so a mapper result that
        # could not determine them must not erase what the CDE declared.
        #
        # nmtc-mapper 0.5.0 made this reachable: is_opportunity_zone is now
        # True-or-None on EVERY path (the designation list is 2010-tract-based
        # while this table and geocoder are 2020-basis, so a non-match and a
        # genuine non-designation are indistinguishable), and the distress /
        # non-metro booleans go None on its indeterminate branches. A straight
        # assignment would overwrite a CDE's correct True with None — the same
        # defect as the native-area read dropped above, in the other direction.
        project.is_high_migration_rural = _prefer_determinate(
            result.is_high_migration_rural, project.is_high_migration_rural
        )
        project.is_opportunity_zone = _prefer_determinate(
            result.is_opportunity_zone, project.is_opportunity_zone
        )
        # is_non_metro (1.4.0 R1) — the OMB Non-Metropolitan County
        # determination, and the field that replaces the twelve-state guess in
        # intelligence/geographic_analysis.
        #
        # It goes through _prefer_determinate for the same reason as the two
        # above, even though no CSV column supplies it today: a pre-enriched
        # pipeline (Pipeline.sample(), every fixture, any caller that populated
        # eligibility itself) can arrive with the field already set, and an
        # indeterminate mapper result must not erase it. Reading it straight
        # would be correct only for as long as nothing else ever writes it,
        # which is the assumption the native-area read was built on.
        project.is_non_metro = _prefer_determinate(
            result.is_non_metro, project.is_non_metro
        )


_INDETERMINATE_DISTRESS = frozenset({"unknown", "unavailable", "", "none"})


def _determinate_distress(value):
    """Return a distress level, or ``None`` if the value means "we don't know".

    nmtc-mapper signals indeterminacy on this field with the STRING "unknown",
    not with ``None``. Stored verbatim it renders as a distress level, and any
    ``is None`` guard downstream — including ``_prefer_determinate`` — misses
    it entirely.

    Example::

        _determinate_distress("deep")     # -> "deep"
        _determinate_distress("unknown")  # -> None
    """
    if value is None:
        return None
    if str(value).strip().lower() in _INDETERMINATE_DISTRESS:
        return None
    return value


def _prefer_determinate(mapper_value, declared):
    """Return the mapper's value unless it is indeterminate.

    Enrichment may correct a CDE's declaration, but it may not erase one:
    a ``None`` from the mapper means "could not determine", which is strictly
    less information than what the CDE supplied on its own pipeline sheet.

    Example::

        _prefer_determinate(None, True)   # -> True  (CDE declaration kept)
        _prefer_determinate(False, True)  # -> False (mapper determined it)
        _prefer_determinate(None, None)   # -> None  (nobody knows)
    """
    if mapper_value is None:
        return declared
    return mapper_value
